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

from entities.player import Player, _item_id, _resolve_item
from entities.companion import Companion
from entities.shadow import Shadow

if TYPE_CHECKING:
    from entities.ally import Ally

MAX_ACTIVE_MEMBERS = 4  # nombre de combattants "sur le terrain" en même temps


class Party:
    def __init__(self, members: list["Ally"] | None = None) -> None:
        self.members: list["Ally"] = members or []          # tous les alliés recrutés (réserve incluse)
        self._active_ids: set[int] = {id(m) for m in self.members[:MAX_ACTIVE_MEMBERS]}
        self.shadows: list[Shadow] = []
        self.assigned_shadow_ids: list[str] = []

    # ---- Accès --------------------------------------------------------
    @property
    def leader(self) -> Player | None:
        """Le Player (celui qui a l'or, l'inventaire, la sauvegarde)."""
        return next((m for m in self.members if isinstance(m, Player)), None)

    @property
    def companions(self) -> list[Companion]:
        return [m for m in self.members if isinstance(m, Companion) and not isinstance(m, Shadow)]

    @property
    def assigned_shadows(self) -> list[Shadow]:
        return [shadow for shadow in self.shadows if shadow.enemy_id in self.assigned_shadow_ids]

    def add_shadow(self, shadow: Shadow) -> bool:
        if any(item.enemy_id == shadow.enemy_id for item in self.shadows):
            return False
        self.shadows.append(shadow)
        return True

    def shadow_for_enemy(self, enemy_id: str) -> Shadow | None:
        return next((shadow for shadow in self.shadows if shadow.enemy_id == enemy_id), None)

    def toggle_shadow_assignment(self, shadow: Shadow) -> bool:
        if shadow.enemy_id in self.assigned_shadow_ids:
            self.assigned_shadow_ids.remove(shadow.enemy_id)
            return False
        if len(self.assigned_shadow_ids) >= self.shadow_slots():
            return False
        self.assigned_shadow_ids.append(shadow.enemy_id)
        return True

    def shadow_slots(self) -> int:
        necromancer = next((m for m in self.members if getattr(m, "class_id", None) == "necromancer"), None)
        return int(getattr(necromancer, "tier_data", {}).get("shadow_slots", 0)) if necromancer else 0

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
            "shadows": [shadow.to_shadow_dict() for shadow in self.shadows],
            "assigned_shadow_ids": list(self.assigned_shadow_ids),
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
        party._load_shadows(data.get("shadows", []), data.get("assigned_shadow_ids", []))
        return party

    def _load_shadows(self, entries: list[dict], assigned: list[str]) -> None:
        import json
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        path = root / "data" / "enemies.json"
        catalog = {entry["id"]: entry for entry in json.loads(path.read_text(encoding="utf-8"))}
        rank_payload = json.loads((root / "data" / "shadow_ranks.json").read_text(encoding="utf-8"))
        ranks = {entry["id"]: entry for entry in rank_payload.get("ranks", [])}
        for entry in entries:
            enemy_id = entry.get("enemy_id")
            if enemy_id in catalog:
                rank_id = entry.get("rank_id", "soldier")
                self.shadows.append(Shadow.from_enemy_data(enemy_id, catalog[enemy_id], entry.get("level", 1), entry.get("xp", 0), rank_id, ranks.get(rank_id, ranks.get("soldier"))))
        owned = {shadow.enemy_id for shadow in self.shadows}
        self.assigned_shadow_ids = [enemy_id for enemy_id in assigned if enemy_id in owned]


# ---- Helpers de (dé)sérialisation pour Companion -------------------------
# (Companion n'a pas encore de to_dict/from_dict dédiés dans entities/companion.py,
#  donc on centralise ça ici pour l'instant plutôt que de dupliquer la logique.)

def _companion_to_dict(companion: Companion) -> dict:
    return {
        "name": companion.name,
        "reward_id": getattr(companion, "reward_id", None),
        "hp": companion.hp,
        "max_hp": companion.base_max_hp,
        "attack": companion.attack,
        "defense": companion.defense,
        "speed": companion.speed,
        "role": companion.role,
        "class_id": companion.class_id,
        "tier": companion.tier,
        "class_node_id": getattr(companion, "class_node_id", None),
        "level": companion.level,
        "xp": companion.xp,
        "weapon_primary": _item_id(companion.weapon_primary),
        "weapon_secondary": _item_id(companion.weapon_secondary),
        "helmet": _item_id(companion.helmet),
        "chest": _item_id(companion.chest),
        "legs": _item_id(companion.legs),
        "boots": _item_id(companion.boots),
        "arms": _item_id(companion.arms),
        "pet": _item_id(companion.pet),
        "inventory": [
            item_id for item_id in (_item_id(item) for item in companion.inventory)
            if item_id is not None
        ],
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
        class_id=data.get("class_id", "warrior"),
        tier=data.get("tier", 1),
        class_node_id=data.get("class_node_id"),
    )
    if data.get("reward_id") is not None:
        companion.reward_id = data["reward_id"]
    companion.hp = data["hp"]
    if data.get("max_hp"):
        companion._saved_hp_ratio = max(0.0, min(1.0, int(data.get("hp", data["max_hp"])) / int(data["max_hp"])))
    companion.weapon_primary = _resolve_item(data.get("weapon_primary"))
    companion.weapon_secondary = _resolve_item(data.get("weapon_secondary"))
    companion.helmet = _resolve_item(data.get("helmet"))
    companion.chest = _resolve_item(data.get("chest"))
    companion.legs = _resolve_item(data.get("legs"))
    companion.boots = _resolve_item(data.get("boots"))
    companion.arms = _resolve_item(data.get("arms"))
    companion.equip_pet(_resolve_item(data.get("pet")))
    companion.inventory = [
        item for item in (_resolve_item(item_id) for item_id in data.get("inventory", []))
        if item is not None
    ]
    return companion
