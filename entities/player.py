"""
entities/player.py

Le personnage contrôlé par l'utilisateur. Son choose_action()
délègue à core/menu.py qui affiche les options et récupère l'input.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from entities.ally import Ally
from entities.combatant import Action, Combatant

if TYPE_CHECKING:
    from items.base import Item


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
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed, level, xp)
        self.gold = gold
        self.inventory: list["Item"] = []

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
            "weapon": self.weapon.id if self.weapon else None,
            "armor": self.armor.id if self.armor else None,
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
        return player
