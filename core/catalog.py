"""
core/catalog.py

Chargement et accès aux catalogues de données du jeu.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Catalogs:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.enemies = self.load("enemies.json")
        self.items = self.load("items.json")
        self.weapons = self.load("weapons.json")
        self.skills = self.load("skills.json")
        self.armors = self.load("armor.json")
        self.pets = self.load("pets.json")
        self.quests = self.load("quests.json")
        self.titles = self.load("titles.json")
        self.regions = self.load("regions.json")
        self.merchants = self.load("merchants.json")

    def load(self, filename: str) -> dict[str, dict[str, Any]]:
        path = self.data_dir / filename
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return {entry["id"]: entry for entry in data if isinstance(entry, dict) and "id" in entry}

    def resolve_item(self, item_id: str | None) -> dict[str, Any] | None:
        if item_id is None:
            return None
        return self.items.get(item_id) or self.weapons.get(item_id) or self.armors.get(item_id) or self.pets.get(item_id)

    def merchant_stock(self) -> dict[str, dict[str, dict[str, dict[str, int]]]]:
        stock_by_merchant: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
        for merchant_id, merchant in self.merchants.items():
            stock: dict[str, dict[str, dict[str, int]]] = {}
            for category, entries in merchant.get("inventory", {}).items():
                stock[category] = {}
                for item_id, values in entries.items():
                    values = values if isinstance(values, dict) else dict(zip(values[::2], values[1::2]))
                    stock[category][item_id] = {
                        "cost": int(values.get("cost", 0)),
                        "quantity": int(values.get("quantity", 0)),
                    }
            stock_by_merchant[merchant_id] = stock
        return stock_by_merchant
