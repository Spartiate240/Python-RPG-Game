"""
entities/merchant.py

Le marchand ne combat pas : il n'hérite PAS de Combatant.
Il gère juste un stock d'items et des prix.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from items.base import Item
    from entities.player import Player


class Merchant:
    def __init__(self, name: str, stock: list["Item"], buyback_rate: float = 0.5) -> None:
        self.name = name
        self.stock = stock              # items disponibles à l'achat
        self.buyback_rate = buyback_rate  # % du prix de base au rachat

    def sell_to(self, player: "Player", item: "Item") -> bool:
        """Le joueur achète `item` au marchand."""
        if item not in self.stock:
            return False
        if not player.spend_gold(item.price):
            return False
        self.stock.remove(item)
        player.add_item(item)
        return True

    def buy_from(self, player: "Player", item: "Item") -> bool:
        """Le joueur revend `item` au marchand."""
        if item not in player.inventory:
            return False
        player.remove_item(item)
        player.gold += int(item.price * self.buyback_rate)
        self.stock.append(item)
        return True
