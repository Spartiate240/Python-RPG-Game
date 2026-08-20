"""
entities/ally.py

Ally = tout ce qui combat du côté du joueur (Player, Companion).
C'est ici que vivent : niveau/xp, équipement, compétences.
Player et Companion héritent de cette classe et ne font que
spécialiser le "cerveau" (choose_action) et quelques attributs.
"""

from __future__ import annotations
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
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed)
        self.level = level
        self.xp = xp

        self.weapon: Any | None = None
        self.helmet: Any | None = None
        self.chest: Any | None = None
        self.legs: Any | None = None
        self.boots: Any | None = None
        self.arms: Any | None = None
        self.skills: list["Skill"] = []

    # ---- Équipement ------------------------------------------------
    def equip_weapon(self, weapon: Any) -> None:
        self.weapon = weapon

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
        bonus = _item_value(self.weapon, ("attack_bonus", "damage"))
        return self.attack + bonus

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
        self.xp += amount
        # Le vrai calcul de palier reste dans progression/level_manager.py
        # (check_level_up(self)) pour ne pas dupliquer la logique ici.

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
