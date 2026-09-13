"""
entities/ally.py

Ally = tout ce qui combat du côté du joueur (Player, Companion).
C'est ici que vivent : niveau/xp, équipement, compétences.
Player et Companion héritent de cette classe et ne font que
spécialiser le "cerveau" (choose_action) et quelques attributs.
"""

from __future__ import annotations
import re
from typing import TYPE_CHECKING, Any

from entities.combatant import Combatant, Action

if TYPE_CHECKING:
    from skills.skills import Skill


class Ally(Combatant):
    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        speed: int,
        level: int = 1,
        xp: int = 0,
        inventory: list[Any] | None = None,
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed)
        self.level = level
        self.xp = xp
        self.inventory: list[Any] = inventory or []

        self.weapon_primary: Any | None = None
        self.weapon_secondary: Any | None = None
        self.helmet: Any | None = None
        self.chest: Any | None = None
        self.legs: Any | None = None
        self.boots: Any | None = None
        self.arms: Any | None = None
        self.pet: Any | None = None
        self.skills: list["Skill"] = []

    # ---- Équipement ------------------------------------------------
    def equip_weapon(self, weapon: Any) -> None:
        self.weapon_primary = weapon

    def equip_weapon_secondary(self, weapon: Any | None) -> None:
        self.weapon_secondary = weapon

    def equip_helmet(self, helmet: Any) -> None:
        self.helmet = helmet

    def equip_chest(self, chest: Any) -> None:
        self.chest = chest

    def equip_legs(self, legs: Any) -> None:
        self.legs = legs

    def equip_boots(self, boots: Any) -> None:
        self.boots = boots

    def equip_arms(self, arms: Any) -> None:
        self.arms = arms

    def equip_pet(self, pet: Any | None) -> None:
        self.pet = pet

    def equip_armor(self, armor: Any) -> None:
        self.equip_chest(armor)

    @property
    def armor(self) -> Any | None:
        return self.chest

    @armor.setter
    def armor(self, value: Any | None) -> None:
        self.chest = value

    @property
    def total_attack(self) -> int:
        bonuses = (
            _item_value(self.weapon_primary, ("attack_bonus", "damage")),
            _item_value(self.weapon_secondary, ("attack_bonus", "damage")),
            _pet_attack_bonus(self.pet),
        )
        return self.attack + sum(bonuses)

    @property
    def total_defense(self) -> int:
        bonuses = (
            _item_value(self.helmet, ("defense_bonus", "defense")),
            _item_value(self.chest, ("defense_bonus", "defense")),
            _item_value(self.legs, ("defense_bonus", "defense")),
            _item_value(self.boots, ("defense_bonus", "defense")),
            _item_value(self.arms, ("defense_bonus", "defense")),
        )
        return self.defense + sum(bonuses)

    # ---- Compétences -------------------------------------------------
    def learn_skill(self, skill: "Skill") -> None:
        if skill not in self.skills:
            self.skills.append(skill)

    # ---- Progression ---------------------------------------------
    def gain_xp(self, amount: int) -> None:
        from progression.level_manager import LevelManager

        LevelManager().add_xp(self, amount)

    # choose_action() reste abstrait : Player (input utilisateur)
    # et Companion (IA) l'implémentent chacun à leur façon.


def _item_value(item: Any | None, keys: tuple[str, ...]) -> int:
    if item is None:
        return 0
    if isinstance(item, dict):
        for key in keys:
            value = item.get(key)
            if isinstance(value, (int, float)):
                return int(value)
        return 0
    for key in keys:
        value = getattr(item, key, None)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def _pet_attack_bonus(pet: Any | None) -> int:
    """Extracts the attack bonus from a pet's data-driven effect."""
    effect = _value(pet, "effect")
    explicit_bonus = _value(pet, "attack_bonus")
    if isinstance(explicit_bonus, (int, float)):
        return int(explicit_bonus)
    if not isinstance(effect, str):
        return 0
    match = re.search(r"attack\s+increased\s+by\s+(\d+)", effect, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _value(item: Any | None, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)
