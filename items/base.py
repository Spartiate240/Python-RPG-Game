"""Modeles metier legers pour les objets du catalogue."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Item:
    id: str
    name: str
    type: str = "item"
    value: int = 0
    rarity: str = "common"
    sprite: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        return item_from_dict(data)


@dataclass
class Equipment(Item):
    slot: str = ""
    attack_bonus: int = 0
    defense_bonus: int = 0
    speed: int = 0
    skills: list[str] = field(default_factory=list)


@dataclass
class Consumable(Item):
    effect: str = ""
    heal: int = 0

    def use(self, target: Any) -> int:
        if self.effect != "heal" or self.heal <= 0:
            return 0
        return target.heal(self.heal)


def item_from_dict(data: dict[str, Any]) -> Item:
    common = {
        "id": str(data["id"]),
        "name": str(data.get("name", data["id"])),
        "type": str(data.get("type", "item")),
        "value": int(data.get("value", 0)),
        "rarity": str(data.get("rarity", "common")),
        "sprite": data.get("sprite"),
    }
    if data.get("effect") == "heal" or data.get("type") == "potion":
        return Consumable(
            **common,
            effect=str(data.get("effect", "")),
            heal=int(data.get("heal", 0)),
        )
    if data.get("slot"):
        return Equipment(
            **common,
            slot=str(data.get("slot", "")),
            attack_bonus=int(data.get("attack_bonus", data.get("damage", 0))),
            defense_bonus=int(data.get("defense_bonus", data.get("defense", 0))),
            speed=int(data.get("speed", 0)),
            skills=list(data.get("skills", [])),
        )
    return Item(**common)
