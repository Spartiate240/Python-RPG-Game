"""
entities/combatant.py

Classe de base ABSTRAITE commune à tout ce qui peut se battre :
Player, Companion (via Ally) et Enemy.

Elle centralise les stats de combat et le contrat que chaque
sous-classe doit respecter (is_alive, choose_action, take_damage...).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional


class Combatant(ABC):
    """Contrat minimal pour participer à un combat (core/fight.py)."""

    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        speed: int,
    ) -> None:
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack = attack
        self.defense = defense
        self.speed = speed

    # ---- État ----------------------------------------------------
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int) -> int:
        """Applique des dégâts (déjà réduits par la défense côté fight.py
        ou ici selon ton choix de design) et renvoie les dégâts réellement subis."""
        dealt = max(0, amount)
        self.hp = max(0, self.hp - dealt)
        return dealt

    def heal(self, amount: int) -> int:
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    # ---- Contrat à implémenter par les sous-classes --------------
    @abstractmethod
    def choose_action(self, allies: list["Combatant"], enemies: list["Combatant"]) -> "Action":
        """Retourne l'action choisie pour ce tour.
        - Player : vient de l'input utilisateur (via core/menu.py)
        - Companion / Enemy : vient d'une IA simple
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name} hp={self.hp}/{self.max_hp}>"


class Action:
    """Petit objet-valeur représentant une action de combat choisie.
    Volontairement simple : fight.py sait comment l'exécuter.
    """

    def __init__(self, kind: str, target: Optional[Combatant] = None, payload: Optional[dict] = None):
        self.kind = kind          # "attack" | "skill" | "item" | "flee" | "defend"
        self.target = target
        self.payload = payload or {}   # ex: {"skill": skill_obj} ou {"item": item_obj}

    def __repr__(self) -> str:
        return f"<Action {self.kind} -> {self.target}>"
