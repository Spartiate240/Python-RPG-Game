"""
entities/player.py

Le personnage contrôlé par l'utilisateur. Son choose_action()
délègue à core/menu.py qui affiche les options et récupère l'input.
"""

from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

from entities.ally import Ally
from entities.combatant import Action, Combatant

if TYPE_CHECKING:
    from items.base import Item


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _load_item_catalog() -> dict[str, dict]:
    catalog: dict[str, dict] = {}
    for filename in ("items.json", "weapons.json", "armor.json"):
        path = DATA_DIR / filename
        if not path.exists():
            continue
        for entry in json.loads(path.read_text(encoding="utf-8")):
            catalog[entry["id"]] = entry
    return catalog


def _item_id(item: object | None) -> str | None:
    if item is None:
        return None
    if isinstance(item, dict):
        return item.get("id")
    return getattr(item, "id", None)


def _resolve_item(item_id: str | None) -> object | None:
    if not item_id:
        return None
    entry = _load_item_catalog().get(item_id)
    if entry is None:
        return item_id
    return SimpleNamespace(**entry)


class Player(Ally):
    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        speed: int,
        level: int = 1,
        xp: int = 0,
        gold: int = 0,
        inventory: list["Item"] = None
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed, level, xp)
        self.gold = gold
        self.inventory: list["Item"] = inventory or []

    # ---- Inventaire / économie -------------------------------------
    def add_item(self, item: "Item") -> None:
        self.inventory.append(item)

    def remove_item(self, item: "Item") -> None:
        if item in self.inventory:
            self.inventory.remove(item)

    def spend_gold(self, amount: int) -> bool:
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False

    # ---- Combat : décidé par l'utilisateur -------------------------
    def choose_action(self, allies: list[Combatant], enemies: list[Combatant]) -> Action:
        from core.menu import Menu  # import local pour éviter le cycle core <-> entities
        return Menu.ask_combat_action(self, allies, enemies)

    # ---- Sauvegarde --------------------------------------------------
    def to_dict(self) -> dict:
        """Sérialisation utilisée pour la sauvegarde du joueur."""
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "level": self.level,
            "xp": self.xp,
            "gold": self.gold,
            "weapon": _item_id(self.weapon),
            "helmet": _item_id(self.helmet),
            "chest": _item_id(self.chest),
            "legs": _item_id(self.legs),
            "boots": _item_id(self.boots),
            "arms": _item_id(self.arms),
            "inventory": [item_id for item in (_item_id(item) for item in self.inventory) if item_id is not None]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        player = cls(
            name=data["name"],
            max_hp=data["max_hp"],
            attack=data["attack"],
            defense=data["defense"],
            speed=data["speed"],
            level=data["level"],
            xp=data["xp"],
            gold=data["gold"],
        )
        player.hp = data["hp"]
        player.weapon = _resolve_item(data.get("weapon"))
        player.helmet = _resolve_item(data.get("helmet"))
        player.chest = _resolve_item(data.get("chest"))
        player.legs = _resolve_item(data.get("legs"))
        player.boots = _resolve_item(data.get("boots"))
        player.arms = _resolve_item(data.get("arms"))
        player.inventory = [
            item for item in (_resolve_item(item_id) for item_id in data.get("inventory", []))
            if item is not None
        ]
        return player
