"""
core/menu.py

Toute l'IO texte du jeu : affichage des menus et lecture des choix
de l'utilisateur. C'est le SEUL endroit qui appelle input()/print()
pour la navigation (le combat en tant que tel reste dans fight.py,
mais menu.py fournit la brique "demander une action au joueur").
"""

from __future__ import annotations
import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from party.party import Party
    from entities.player import Player
    from entities.combatant import Combatant, Action


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class Menu:
    # ---- Menus généraux ------------------------------------------------
    def show_main_menu(self) -> str:
        print("\n=== MENU PRINCIPAL ===")
        print("1. Nouvelle partie")
        print("2. Charger la partie")
        print("3. Quitter")
        choice = input("> ").strip()
        return {"1": "new_game", "2": "load_game", "3": "quit"}.get(choice, "new_game")

    def show_exploration_menu(self, party: "Party") -> str:
        print(f"\n=== EXPLORATION === (Or: {party.leader.gold if party.leader else 0})")
        print("1. Avancer (risque de rencontre)")
        print("2. Aller à la boutique")
        print("3. Voir l'état du groupe")
        print("4. Sauvegarder")
        print("5. Sauvegarder et quitter")
        choice = input("> ").strip()
        return {"1": "encounter", "2": "shop", "3": "party_status", "4": "save", "5": "quit"}.get(choice, "encounter")

    def show_shop_menu(self, party: "Party") -> None:
        print("\n=== BOUTIQUE ===")
        print("(à implémenter avec entities/merchant.py)")

    def show_game_over(self) -> None:
        print("\n=== GAME OVER ===")

    # ---- Combat : demande d'action au joueur --------------------------
    @staticmethod
    def ask_combat_action(player: "Player", allies: list["Combatant"], enemies: list["Combatant"]) -> "Action":
        from entities.combatant import Action

        print(f"\n--- Tour de {player.name} (HP: {player.hp}/{player.max_hp}) ---")
        Menu._show_combat_state(allies, enemies)
        print("1. Attaquer")
        print("2. Compétence")
        print("3. Objet")
        choice = input("> ").strip()

        living_enemies = [e for e in enemies if e.is_alive()]

        if choice == "1" and living_enemies:
            target = Menu._pick_target(living_enemies)
            return Action("attack", target=target)

        if choice == "2" and player.skills:
            skill = Menu._pick_skill(player)
            target = Menu._pick_target(living_enemies) if living_enemies else None
            return Action("skill", target=target, payload={"skill": skill})

        if choice == "3" and player.inventory:
            item = Menu._pick_item(player)
            return Action("item", target=player, payload={"item": item})

    @staticmethod
    def _pick_target(candidates: list["Combatant"]) -> "Combatant":
        print("Cible :")
        for i, c in enumerate(candidates, 1):
            print(f"{i}. {c.name} (HP: {c.hp}/{c.max_hp})")
        idx = input("> ").strip()
        try:
            return candidates[int(idx) - 1]
        except (ValueError, IndexError):
            return candidates[0]

    @staticmethod
    def _pick_skill(player: "Player"):
        print("Compétence :")
        for i, s in enumerate(player.skills, 1):
            print(f"{i}. {s.name}")
        idx = input("> ").strip()
        try:
            return player.skills[int(idx) - 1]
        except (ValueError, IndexError):
            return player.skills[0]

    @staticmethod
    def _pick_item(player: "Player"):
        print("Objet :")
        for i, it in enumerate(player.inventory, 1):
            print(f"{i}. {it.name}")
        idx = input("> ").strip()
        try:
            return player.inventory[int(idx) - 1]
        except (ValueError, IndexError):
            return player.inventory[0]

    @staticmethod
    def _show_combat_state(allies: list["Combatant"], enemies: list["Combatant"]) -> None:
        print("Alliés :")
        for combatant in allies:
            status = "KO" if not combatant.is_alive() else f"HP: {combatant.hp}/{combatant.max_hp}"
            print(f"- {combatant.name} ({status})")

        print("Ennemis :")
        for combatant in enemies:
            status = "KO" if not combatant.is_alive() else f"HP: {combatant.hp}/{combatant.max_hp}"
            print(f"- {combatant.name} ({status})")

    # ---- Inventaire : demande d'action au joueur --------------------------
    def show_party_status(self, party: "Party") -> None:
        print("\n=== ÉTAT DU GROUPE ===")
        for member in party.members:
            status = "KO" if not member.is_alive() else f"HP: {member.hp}/{member.max_hp}"
            print(f"- {member.name} ({status})")
    
    def _show_inventory(self, party: "Party", inventory: dict[str, dict[str, int]]) -> None:
        player = party.leader
        if player is None:
            print("\n=== INVENTAIRE ===")
            print("Aucun joueur dans le groupe.")
            return

        print("\n=== INVENTAIRE ===")
        self._show_equipment(player)
        self._show_stock(inventory)

        while True:
            print("\n1. Changer l'équipement")
            print("2. Retour")
            choice = input("> ").strip()
            if choice == "2":
                return
            if choice == "1":
                self._equip_from_inventory(player, inventory)
                return

    @staticmethod
    def _show_equipment(player: "Player") -> None:
        print("\nÉquipement actuel :")
        print(f"- Arme: {Menu._item_label(player.weapon)}")
        print(f"- Tête: {Menu._item_label(player.helmet)}")
        print(f"- Torse: {Menu._item_label(player.chest)}")
        print(f"- Jambes: {Menu._item_label(player.legs)}")
        print(f"- Pieds: {Menu._item_label(player.boots)}")
        print(f"- Bras: {Menu._item_label(player.arms)}")

    @staticmethod
    def _show_stock(inventory: dict[str, dict[str, int]]) -> None:
        print("\nStock :")
        has_items = False
        for category in ("items", "weapons", "armors"):
            entries = inventory.get(category, {})
            if not entries:
                continue
            has_items = True
            print(f"{category.capitalize()}:")
            for item_id, quantity in entries.items():
                item = Menu._resolve_item(item_id)
                label = Menu._item_label(item) if item is not None else item_id
                print(f"- {label} x{quantity}")
        if not has_items:
            print("Aucun objet.")

    def _equip_from_inventory(self, player: "Player", inventory: dict[str, dict[str, int]]) -> None:
        options: list[object] = []
        for category in ("weapons", "armors"):
            for item_id, quantity in inventory.get(category, {}).items():
                if quantity > 0:
                    item = self._resolve_item(item_id)
                    if item is not None:
                        options.append(item)

        if not options:
            print("Aucun équipement disponible.")
            return

        print("\nChoisir un équipement :")
        for index, item in enumerate(options, 1):
            print(f"{index}. {self._item_label(item)}")

        choice = input("> ").strip()
        try:
            selected = options[int(choice) - 1]
        except (ValueError, IndexError):
            selected = options[0]

        self._apply_equipment(player, inventory, selected)


    @staticmethod
    def _remove_equipment(player: "Player", inventory: dict[str, dict[str, int]], slot: str) -> None:
        if slot == "weapon":
            Menu._add_to_inventory(inventory, player.weapon)
            player.equip_weapon(None)
        elif slot == "helmet":
            Menu._add_to_inventory(inventory, player.helmet)
            player.equip_helmet(None)
        elif slot == "chest":
            Menu._add_to_inventory(inventory, player.chest)
            player.equip_chest(None)
        elif slot == "legs":
            Menu._add_to_inventory(inventory, player.legs)
            player.equip_legs(None)
        elif slot == "boots":
            Menu._add_to_inventory(inventory, player.boots)
            player.equip_boots(None)
        elif slot == "arms":
            Menu._add_to_inventory(inventory, player.arms)
            player.equip_arms(None)

    @staticmethod
    def _apply_equipment(player: "Player", inventory: dict[str, dict[str, int]], item: object) -> None:
        slot = Menu._item_slot(item)
        Menu._remove_equipment(player, inventory, slot)
        Menu._remove_from_inventory(inventory, item)
        
        if Menu._is_weapon(item):
            player.equip_weapon(item)
            print(f"{Menu._item_label(item)} équipé.")
            return

        if slot == "chest":
            player.equip_chest(item)
        elif slot == "helmet":
            player.equip_helmet(item)
        elif slot == "legs":
            player.equip_legs(item)
        elif slot == "boots":
            player.equip_boots(item)
        elif slot == "arms":
            player.equip_arms(item)
        else:
            print("Cet objet ne peut pas être équipé.")
            return

        print(f"{Menu._item_label(item)} équipé.")

    @staticmethod
    def _remove_from_inventory(inventory: dict[str, dict[str, int]], item: object) -> None:
        item_id = Menu._item_id(item)
        category = Menu._item_category(item)
        if item_id is None or category is None:
            return
        entries = inventory.get(category)
        if not entries:
            return
        quantity = entries.get(item_id, 0)
        if quantity <= 1:
            entries.pop(item_id, None)
        else:
            entries[item_id] = quantity - 1

    @staticmethod
    def _add_to_inventory(inventory: dict[str, dict[str, int]], item: object | None) -> None:
        if item is None:
            return
        item_id = Menu._item_id(item)
        category = Menu._item_category(item)
        if item_id is None or category is None:
            return
        entries = inventory.setdefault(category, {})
        entries[item_id] = entries.get(item_id, 0) + 1

    @staticmethod
    def _resolve_item(item_id: str) -> object | None:
        for filename in ("items.json", "weapons.json", "armor.json"):
            path = DATA_DIR / filename
            if not path.exists():
                continue
            for entry in json.loads(path.read_text(encoding="utf-8")):
                if entry.get("id") == item_id:
                    return SimpleNamespace(**entry)
        return None

    @staticmethod
    def _item_label(item: object | None) -> str:
        if item is None:
            return "Aucun"
        if isinstance(item, dict):
            return item.get("name", item.get("id", "Inconnu"))
        return getattr(item, "name", getattr(item, "id", "Inconnu"))

    @staticmethod
    def _item_type(item: object | None) -> str:
        if item is None:
            return ""
        if isinstance(item, dict):
            return str(item.get("type", ""))
        return str(getattr(item, "type", ""))

    @staticmethod
    def _item_slot(item: object | None) -> str:
        if item is None:
            return ""
        if isinstance(item, dict):
            return str(item.get("slot", ""))
        return str(getattr(item, "slot", ""))

    @staticmethod
    def _item_id(item: object | None) -> str | None:
        if item is None:
            return None
        if isinstance(item, dict):
            return item.get("id")
        return getattr(item, "id", None)

    @staticmethod
    def _item_category(item: object | None) -> str | None:
        if Menu._is_weapon(item):
            return "weapons"
        if Menu._item_slot(item):
            return "armors"
        if Menu._item_type(item):
            return "items"
        return None

    @staticmethod
    def _is_weapon(item: object | None) -> bool:
        if item is None:
            return False
        if isinstance(item, dict):
            return "damage" in item and not item.get("slot")
        return hasattr(item, "damage") and not getattr(item, "slot", None)