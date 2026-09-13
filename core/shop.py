"""Services de boutique, sans dependance a pygame."""

from __future__ import annotations

from typing import Any

from core.inventory import InventoryManager
from party.party import Party


class ShopService:
    """Gere les achats dans le stock catalogue d'un marchand."""

    def __init__(self, catalogs: Any, merchant_stock: dict[str, Any]) -> None:
        self.catalogs = catalogs
        self.merchant_stock = merchant_stock
        self.party: Party | None = None
        self.inventory_manager: InventoryManager | None = None

    def bind(
        self,
        party: Party | None,
        inventory_manager: InventoryManager,
        merchant_stock: dict[str, Any] | None = None,
    ) -> None:
        self.party = party
        self.inventory_manager = inventory_manager
        if merchant_stock is not None:
            self.merchant_stock = merchant_stock

    def buy(self, merchant_id: str | None, category: str, item_id: str) -> str:
        if merchant_id is None:
            return "Cet objet n'est pas disponible."

        item = self.catalogs.resolve_item(item_id)
        entry = self.merchant_stock.get(merchant_id, {}).get(category, {}).get(item_id)
        leader = self.party.leader if self.party else None
        if item is None or entry is None or leader is None:
            return "Cet objet n'est pas disponible."

        cost = int(entry.get("cost", 0))
        if int(entry.get("quantity", 0)) <= 0:
            return "Cet objet est épuisé."
        if not leader.spend_gold(cost):
            return "Pas assez d'or."

        entry["quantity"] = int(entry["quantity"]) - 1
        if self.inventory_manager is not None:
            self.inventory_manager.add_shared_item(item)
        return f"{item.get('name', item_id)} acheté."
