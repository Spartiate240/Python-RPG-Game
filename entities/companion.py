"""
entities/companion.py

Allié recruté (pas le joueur). Il combat automatiquement selon
un rôle simple : "attacker", "healer", "support"...
"""

from __future__ import annotations
import random

from entities.ally import Ally
from entities.combatant import Action, Combatant


class Companion(Ally):
    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        speed: int,
        role: str = "attacker",
        level: int = 1,
        xp: int = 0,
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed, level, xp)
        self.role = role  # pilote l'IA de choose_action

    # ---- IA simple ----------------------------------------------
    def choose_action(self, allies: list[Combatant], enemies: list[Combatant]) -> Action:
        living_enemies = [e for e in enemies if e.is_alive()]

        if self.role == "healer":
            wounded = [a for a in allies if a.is_alive() and a.hp < a.max_hp]
            if wounded and self.skills:
                target = min(wounded, key=lambda a: a.hp / a.max_hp)
                heal_skill = next((s for s in self.skills if s.kind == "heal"), None)
                if heal_skill:
                    return Action("skill", target=target, payload={"skill": heal_skill})

        # comportement par défaut : attaquer l'ennemi le plus faible
        if living_enemies:
            target = min(living_enemies, key=lambda e: e.hp)
            return Action("attack", target=target)

        return Action("defend")
