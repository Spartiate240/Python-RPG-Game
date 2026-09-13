"""
core/inventory.py

Gestion de l'inventaire partage et de l'equipement, sans dependance a pygame.
"""

from __future__ import annotations

from typing import Any

from party.party import Party


class InventoryManager:
    def __init__(self, pet_catalog: dict[str, dict[str, Any]]) -> None:
        self.pet_catalog = pet_catalog
        self.party: Party | None = None
        self.inventory: dict[str, dict[str, int]] = {}
        self.selected_member_index = 0

    def bind(self, party: Party | None, inventory: dict[str, dict[str, int]]) -> None:
        self.party = party
        self.inventory = inventory

    def selected_member(self) -> Any | None:
        if self.party is None or not self.party.members:
            return None
        if not 0 <= self.selected_member_index < len(self.party.members):
            self.selected_member_index = 0
        return self.party.members[self.selected_member_index]

    @staticmethod
    def item_label(item: object | None) -> str:
        if item is None:
            return "Aucun"
        if isinstance(item, dict):
            return str(item.get("name", item.get("id", "Inconnu")))
        return str(getattr(item, "name", getattr(item, "id", "Inconnu")))

    @staticmethod
    def item_slot(item: object | None) -> str:
        if item is None:
            return ""
        if isinstance(item, dict):
            return str(item.get("slot", ""))
        return str(getattr(item, "slot", ""))

    @staticmethod
    def item_id(item: object | None) -> str | None:
        if item is None:
            return None
        if isinstance(item, dict):
            return item.get("id")
        return getattr(item, "id", None)

    @staticmethod
    def item_stat(item: object, *names: str) -> object | None:
        if isinstance(item, dict):
            for name in names:
                if name in item:
                    return item[name]
            return None
        for name in names:
            value = getattr(item, name, None)
            if value is not None:
                return value
        return None

    def item_details(self, item: object) -> list[str]:
        details: list[str] = []
        stat_labels = (
            ("ATQ", ("attack_bonus", "damage")),
            ("DEF", ("defense_bonus", "defense")),
            ("PV", ("health", "max_health")),
            ("Vitesse", ("speed",)),
            ("Niveau requis", ("level_required", "required_level")),
            ("Rareté", ("rarity",)),
            ("Effet", ("effect",)),
        )
        for label, names in stat_labels:
            value = self.item_stat(item, *names)
            if value is not None:
                details.append(f"{label}: {value}")
        return details

    @staticmethod
    def is_weapon(item: object | None) -> bool:
        if item is None:
            return False
        if isinstance(item, dict):
            return item.get("slot") == "weapon" or ("damage" in item and not item.get("slot"))
        return getattr(item, "slot", "") == "weapon" or (hasattr(item, "damage") and not getattr(item, "slot", None))

    def is_pet(self, item: object | None) -> bool:
        return self.item_id(item) in self.pet_catalog

    def shared_category(self, item: object) -> str:
        if self.is_pet(item):
            return "pets"
        return "weapons" if self.is_weapon(item) else "armors" if self.item_slot(item) else "items"

    def is_equippable(self, item: object) -> bool:
        return self.is_pet(item) or self.is_weapon(item) or self.item_slot(item) in {
            "helmet", "chest", "legs", "boots", "arms"
        }

    def add_shared_item(self, item: object | None) -> None:
        item_id = self.item_id(item)
        if item_id is None:
            return
        category = self.shared_category(item)
        entries = self.inventory.setdefault(category, {})
        entries[item_id] = int(entries.get(item_id, 0)) + 1

    def consume_stock_item(self, item: object) -> bool:
        item_id = self.item_id(item)
        if item_id is None:
            return False
        entries = self.inventory.get(self.shared_category(item), {})
        quantity = int(entries.get(item_id, 0))
        if quantity <= 0:
            return False
        if quantity == 1:
            del entries[item_id]
        else:
            entries[item_id] = quantity - 1
        return True

    def merge_member_inventories(self) -> None:
        if self.party is None:
            return
        for member in self.party.members:
            for item in member.inventory:
                self.add_shared_item(item)
            member.inventory.clear()

    def equip_item(self, item: object | None) -> str | None:
        player = self.selected_member()
        if player is None or item is None or self.item_id(item) is None:
            return None

        if item in player.inventory:
            player.inventory.remove(item)

        slot = self.item_slot(item)
        if self.is_pet(item):
            if player.pet is not None:
                self.add_shared_item(player.pet)
            player.equip_pet(item)
            return f"{self.item_label(item)} équipé."

        if self.is_weapon(item):
            if player.weapon_primary is None:
                player.equip_weapon(item)
                slot_label = "arme principale"
            elif player.weapon_secondary is None:
                player.equip_weapon_secondary(item)
                slot_label = "arme secondaire"
            else:
                self.add_shared_item(player.weapon_primary)
                player.equip_weapon(item)
                slot_label = "arme principale"
            return f"{self.item_label(item)} équipé en {slot_label}."

        slot_methods = {
            "helmet": "equip_helmet",
            "chest": "equip_chest",
            "legs": "equip_legs",
            "boots": "equip_boots",
            "arms": "equip_arms",
        }
        equip_method = slot_methods.get(slot)
        if equip_method is None:
            return "Cet objet ne peut pas être équipé."
        previous_item = getattr(player, slot, None)
        if previous_item is not None:
            self.add_shared_item(previous_item)
        getattr(player, equip_method)(None)
        getattr(player, equip_method)(item)
        return f"{self.item_label(item)} équipé."

    def unequip_slot(self, slot: str) -> str | None:
        player = self.selected_member()
        if player is None:
            return None

        slots = {
            "weapon_primary": ("weapon_primary", "equip_weapon", "Arme principale retirée."),
            "weapon_secondary": ("weapon_secondary", "equip_weapon_secondary", "Arme secondaire retirée."),
            "helmet": ("helmet", "equip_helmet", "Tête retirée."),
            "chest": ("chest", "equip_chest", "Torse retiré."),
            "legs": ("legs", "equip_legs", "Jambes retirées."),
            "boots": ("boots", "equip_boots", "Bottes retirées."),
            "arms": ("arms", "equip_arms", "Bras retirés."),
            "pet": ("pet", "equip_pet", "Compagnon retiré."),
        }
        attribute, equip_method, feedback = slots.get(slot, ("", "", ""))
        item = getattr(player, attribute, None)
        if item is None:
            return None
        self.add_shared_item(item)
        getattr(player, equip_method)(None)
        return feedback
