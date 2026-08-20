"""
entities/ally.py

Ally = tout ce qui combat du côté du joueur (Player, Companion).
C'est ici que vivent : niveau/xp, équipement, compétences.
Player et Companion héritent de cette classe et ne font que
spécialiser le "cerveau" (choose_action) et quelques attributs.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from entities.combatant import Combatant, Action

if TYPE_CHECKING:
    from items.weapon import Weapon
    from items.armor import Armor
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

        self.weapon: Optional["Weapon"] = None
        self.armor: Optional["Armor"] = None
        self.skills: list["Skill"] = []

    # ---- Équipement ------------------------------------------------
    def equip_weapon(self, weapon: "Weapon") -> None:
        self.weapon = weapon

    def equip_armor(self, armor: "Armor") -> None:
        self.armor = armor

    @property
    def total_attack(self) -> int:
        bonus = self.weapon.attack_bonus if self.weapon else 0
        return self.attack + bonus

    @property
    def total_defense(self) -> int:
        bonus = self.armor.defense_bonus if self.armor else 0
        return self.defense + bonus

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
