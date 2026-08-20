"""
core/menu.py

Toute l'IO texte du jeu : affichage des menus et lecture des choix
de l'utilisateur. C'est le SEUL endroit qui appelle input()/print()
pour la navigation (le combat en tant que tel reste dans fight.py,
mais menu.py fournit la brique "demander une action au joueur").
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from party.party import Party
    from entities.player import Player
    from entities.combatant import Combatant, Action


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
        print("3. Sauvegarder")
        print("4. Sauvegarder et quitter")
        choice = input("> ").strip()
        return {"1": "encounter", "2": "shop", "3": "save", "4": "quit"}.get(choice, "encounter")

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
        print("4. Défendre")
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

        return Action("defend")

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
