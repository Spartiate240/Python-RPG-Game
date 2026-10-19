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
        self.ranks = self.load("adventurerer_rank.json")
        self.classes = self.load_classes()
        self.quests = self.load("quests.json")
        self._add_rank_evaluation_quests()
        self._add_class_trial_quests()
        self.titles = self.load("titles.json")
        self.regions = self.load("regions.json")
        self.merchants = self.load("merchants.json")
        self.dialogues = self.load_dialogues()

    def _add_rank_evaluation_quests(self) -> None:
        rank_entries = list(self.ranks.values())
        for index, rank in enumerate(rank_entries[1:], start=1):
            quest_id = f"rank_evaluation_{rank['id']}"
            previous_rank = rank_entries[index - 1]
            self.quests.setdefault(quest_id, {
                "id": quest_id,
                "type": "unique",
                "name": f"Évaluation de rang {rank['name']}",
                "description": f"Vainquez l'adversaire d'évaluation pour atteindre le rang {rank['name']}.",
                "conditions": [
                    {"type": "level", "target": int(rank.get("min_level", 1))},
                    {"type": "min_rank", "rank": previous_rank["id"]},
                    {"type": "defeat_enemy", "enemy_id": rank.get("evaluation_enemy"), "target": 1},
                ],
                "rewards": {"rank_up": rank["id"]},
                "evaluation_rank": rank["id"],
                "evaluation_enemy": rank.get("evaluation_enemy"),
            })

    def _add_class_trial_quests(self) -> None:
        for class_id, class_data in self.classes.items():
            for tier in class_data.get("tiers", [])[1:]:
                quest_id = str(tier.get("requirements", {}).get("quest_id", ""))
                if not quest_id:
                    continue
                enemy_id = f"{class_id}_trial_{tier['tier']}"
                requirements = tier.get("requirements", {})
                self.quests.setdefault(quest_id, {
                    "id": quest_id,
                    "type": "unique",
                    "name": f"Épreuve : {class_data['name']} {tier['name']}",
                    "description": f"Vainquez l'adversaire de l'épreuve pour devenir {tier['name']}.",
                    "conditions": [
                        {"type": "level", "target": int(requirements.get("min_level", 1))},
                        {"type": "min_rank", "rank": requirements.get("min_rank", "iron")},
                        {"type": "defeat_enemy", "enemy_id": enemy_id, "target": 1},
                    ],
                    "rewards": {"tier_up": {"class_id": class_id, "tier": int(tier["tier"])}},
                    "class_trial": True,
                    "class_id": class_id,
                    "tier": int(tier["tier"]),
                    "evaluation_enemy": enemy_id,
                })

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

    def load_classes(self) -> dict[str, dict[str, Any]]:
        data = json.loads((self.data_dir / "classes.json").read_text(encoding="utf-8"))
        return {
            str(entry.get("id", entry.get("line_id"))): {"id": entry.get("id", entry.get("line_id")), **entry}
            for entry in data
            if isinstance(entry, dict) and entry.get("id", entry.get("line_id"))
        }

    def load_dialogues(self) -> dict[str, dict[str, Any]]:
        path = self.data_dir / "dialogues.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return {str(dialogue_id): entry for dialogue_id, entry in data.items() if isinstance(entry, dict)}

    def region_for_zone(self, zone_id: str | None) -> str | None:
        if zone_id is None:
            return None
        for region_id, region in self.regions.items():
            if any(zone.get("id") == zone_id for zone in region.get("zones", [])):
                return region_id
        return None

    def zone_for_id(self, zone_id: str | None) -> dict[str, Any] | None:
        if zone_id is None:
            return None
        for region in self.regions.values():
            for zone in region.get("zones", []):
                if zone.get("id") == zone_id:
                    return zone
        return None

    def zone_belongs_to_region(self, region_id: str | None, zone_id: str) -> bool:
        region = self.regions.get(region_id or "", {})
        return any(zone.get("id") == zone_id for zone in region.get("zones", []))

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
