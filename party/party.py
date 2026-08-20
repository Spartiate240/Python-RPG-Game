"""
party/party.py

Regroupe les Ally (Player + Companion) recrutés par le joueur et
gère qui est "sur le terrain" (actif en combat) vs en réserve.

C'est cette classe qui est manipulée par core/game.py (state) et
core/fight.py (combat), sans qu'ils aient à savoir si un membre
est le héros ou un compagnon.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from entities.player import Player
from entities.companion import Companion

if TYPE_CHECKING:
    from entities.ally import Ally

MAX_ACTIVE_MEMBERS = 4  # nombre de combattants "sur le terrain" en même temps


class Party:
    def __init__(self, members: list["Ally"] | None = None) -> None:
        self.members: list["Ally"] = members or []          # tous les alliés recrutés (réserve incluse)
        self._active_ids: set[int] = {id(m) for m in self.members[:MAX_ACTIVE_MEMBERS]}

    # ---- Accès --------------------------------------------------------
    @property
    def leader(self) -> Player | None:
        """Le Player (celui qui a l'or, l'inventaire, la sauvegarde)."""
        return next((m for m in self.members if isinstance(m, Player)), None)

    @property
    def companions(self) -> list[Companion]:
        return [m for m in self.members if isinstance(m, Companion)]

    def active_members(self) -> list["Ally"]:
        """Alliés participant au combat / à l'affichage terrain."""
        return [m for m in self.members if id(m) in self._active_ids]

    def reserve_members(self) -> list["Ally"]:
        return [m for m in self.members if id(m) not in self._active_ids]

    def is_wiped(self) -> bool:
        return not any(m.is_alive() for m in self.active_members())

    # ---- Gestion des membres -------------------------------------------
    def recruit(self, ally: "Ally") -> None:
        self.members.append(ally)
        if len(self._active_ids) < MAX_ACTIVE_MEMBERS:
            self._active_ids.add(id(ally))

    def dismiss(self, ally: "Ally") -> None:
        if ally in self.members:
            self.members.remove(ally)
            self._active_ids.discard(id(ally))

    def set_active(self, ally: "Ally") -> bool:
        """Fait entrer `ally` sur le terrain (échange avec un membre actif si complet)."""
        if ally not in self.members:
            return False
        if len(self._active_ids) >= MAX_ACTIVE_MEMBERS and id(ally) not in self._active_ids:
            # on retire le premier actif qui n'est pas le leader pour faire de la place
            for current in self.active_members():
                if not isinstance(current, Player):
                    self._active_ids.discard(id(current))
                    break
        self._active_ids.add(id(ally))
        return True

    def set_reserve(self, ally: "Ally") -> None:
        self._active_ids.discard(id(ally))

    # ---- Persistance ----------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "members": [
                {"type": "player", **m.to_dict()} if isinstance(m, Player)
                else {"type": "companion", **_companion_to_dict(m)}
                for m in self.members
            ],
            "active_indexes": [
                i for i, m in enumerate(self.members) if id(m) in self._active_ids
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Party":
        members: list["Ally"] = []
        for entry in data.get("members", []):
            if entry["type"] == "player":
                members.append(Player.from_dict(entry))
            else:
                members.append(_companion_from_dict(entry))

        party = cls(members=[])  # on construit vide puis on remplit pour contrôler les actifs
        party.members = members
        active_indexes = data.get("active_indexes", list(range(min(len(members), MAX_ACTIVE_MEMBERS))))
        party._active_ids = {id(members[i]) for i in active_indexes if i < len(members)}
        return party


# ---- Helpers de (dé)sérialisation pour Companion -------------------------
# (Companion n'a pas encore de to_dict/from_dict dédiés dans entities/companion.py,
#  donc on centralise ça ici pour l'instant plutôt que de dupliquer la logique.)

def _companion_to_dict(companion: Companion) -> dict:
    return {
        "name": companion.name,
        "hp": companion.hp,
        "max_hp": companion.max_hp,
        "attack": companion.attack,
        "defense": companion.defense,
        "speed": companion.speed,
        "role": companion.role,
        "level": companion.level,
        "xp": companion.xp,
    }


def _companion_from_dict(data: dict) -> Companion:
    companion = Companion(
        name=data["name"],
        max_hp=data["max_hp"],
        attack=data["attack"],
        defense=data["defense"],
        speed=data["speed"],
        role=data.get("role", "attacker"),
        level=data.get("level", 1),
        xp=data.get("xp", 0),
    )
    companion.hp = data["hp"]
    return companion
