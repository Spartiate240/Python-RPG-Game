"""
core/gui.py

Interface pygame du jeu. Elle réutilise les modèles existants
pour la sauvegarde et le combat.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pygame

from core.battle import Battle
from core.catalog import Catalogs
from core.game import Game, GameState
from core.encounter import EncounterService
from core.inventory import InventoryManager
from core.progression import ProgressionManager
from core.shop import ShopService
from entities.player import Player
from party.party import Party
from ui.battle import BattleScreen
from ui.exploration import ExplorationScreen
from ui.game_over import GameOverScreen
from ui.main_menu import MainMenuScreen
from ui.quests import QuestsScreen
from ui.regions import RegionsScreen
from ui.renderer import UIRenderer
from ui.shop import ShopScreen
from ui.status import StatusScreen
from ui.theme import PANEL, TEXT
from ui.titles import TitlesScreen
from ui.widgets import Button
from ui.zones import ZonesScreen


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SCREEN_SIZE = (1280, 720)

# LAYOUT STATUT
# Déplacer ces valeurs suffit à recentrer les colonnes, les boutons et le bandeau
# de retour sans avoir à modifier chaque coordonnée une par une dans le code.
STATUS_PANEL_RECT = pygame.Rect(50, 60, 1180, 620)
STATUS_LEFT_X = 200
STATUS_RIGHT_X = 665
STATUS_TITLE_Y = 100
STATUS_HINT_Y = 145
STATUS_CONTENT_Y = 200
STATUS_ROW_GAP = 44
STATUS_ITEM_ROW_GAP = 36
STATUS_COLUMN_W = 410
STATUS_EQUIPPED_Y = STATUS_CONTENT_Y + 36
STATUS_EQUIPPED_BOX_SIZE = 56
STATUS_EQUIPPED_GAP = 10
STATUS_INVENTORY_TITLE_Y = STATUS_EQUIPPED_Y + STATUS_EQUIPPED_BOX_SIZE + 22
STATUS_INVENTORY_Y = STATUS_INVENTORY_TITLE_Y + 36
STATUS_BACK_BUTTON_RECT = pygame.Rect(1075, 610, 130, 56)
STATUS_FEEDBACK_RECT = pygame.Rect(95, 600, 950, 48)
STATUS_LABEL_ICON_SIZE = (24, 24)
STATUS_ITEM_ICON_SIZE = (28, 28)


SHOP_BACK_BUTTON_RECT = pygame.Rect(1075, 610, 130, 56)
SHOP_PANEL_RECT = pygame.Rect(60, 70, 1160, 580)
SHOP_MERCHANT_BUTTON_RECT = pygame.Rect(150, 205, 980, 70)
SHOP_ITEM_BUTTON_X = 130
SHOP_ITEM_BUTTON_W = 700
SHOP_ITEM_BUTTON_H = 48
SHOP_ITEM_START_Y = 190
SHOP_ITEM_ROW_GAP = 58
QUESTS_PANEL_RECT = pygame.Rect(70, 55, 1140, 610)
QUESTS_BOARD_RECT = pygame.Rect(105, 125, 1070, 470)
QUESTS_BACK_BUTTON_RECT = pygame.Rect(1035, 610, 150, 48)
TITLES_PANEL_RECT = pygame.Rect(70, 55, 1140, 610)
TITLES_BACK_BUTTON_RECT = pygame.Rect(1035, 610, 150, 48)


class PygameApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Python RPG")
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        self.clock = pygame.time.Clock()
        # Police serif pour renforcer l'impression parchemin / chronique.
        self.font = pygame.font.SysFont("dejavuserif", 24)
        self.font_small = pygame.font.SysFont("dejavuserif", 18)
        self.font_big = pygame.font.SysFont("dejavuserif", 40, bold=True)
        self.font_huge = pygame.font.SysFont("dejavuserif", 58, bold=True)
        self.main_menu_screen = MainMenuScreen()
        self.battle_screen = BattleScreen()
        self.exploration_screen = ExplorationScreen()
        self.game_over_screen = GameOverScreen()
        self.regions_screen = RegionsScreen()
        self.zones_screen = ZonesScreen()
        self.shop_screen = ShopScreen()
        self.status_screen = StatusScreen()
        self.quests_screen = QuestsScreen()
        self.titles_screen = TitlesScreen()
        self.core = Game()
        self.state = "main_menu"
        self.party: Party | None = None
        self.location: str | None = None
        self.selected_region_id: str | None = None
        self.inventory: dict[str, dict[str, int]] = {"items": {}, "weapons": {}, "armors": {}, "pets": {}}
        self.battle: Battle | None = None
        self.selected_battle_action = "attack"
        self.selected_battle_skill_id: str | None = None
        # Message court pour confirmer une action d'équipement ou de retrait.
        self.status_feedback = ""
        # Personnage actuellement sélectionné dans l'écran statut (index dans party.members).
        self.selected_member_index = 0
        # Les sprites UI existent sous deux formes:
        # - fichiers extraits, faciles à charger directement;
        # - spritesheet + manifeste, utiles si le sprite extrait n'existe pas encore.
        # On garde les deux voies pour que l'UI puisse grandir sans réécriture.
        self.ui_sprite_cache: dict[tuple[str, str, tuple[int, int] | None], pygame.Surface] = {}
        self.ui_sheet_cache: dict[str, pygame.Surface] = {}
        self.ui_manifest_cache: dict[str, list[dict[str, Any]]] = {}
        self.sprite_cache: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}
        self.renderer = UIRenderer(self)
        self.catalogs = Catalogs(DATA_DIR)
        self.encounter_service = EncounterService(self.catalogs)
        self.enemy_catalog = self.catalogs.enemies
        self.item_catalog = self.catalogs.items
        self.weapon_catalog = self.catalogs.weapons
        self.armor_catalog = self.catalogs.armors
        self.pet_catalog = self.catalogs.pets
        self.quest_catalog = self.catalogs.quests
        self.title_catalog = self.catalogs.titles
        self.region_catalog = self.catalogs.regions
        self.merchant_catalog = self.catalogs.merchants
        self.merchant_stock = self.catalogs.merchant_stock()
        self.selected_merchant_id: str | None = None
        self.progression: dict[str, Any] = {
            "stats": {"victories": 0, "gold_earned": 0, "quests_completed": 0},
            "quests": {"active": [], "completed": [], "claimed": []},
            "titles": {},
        }
        self.inventory_manager = InventoryManager(self.pet_catalog)
        self.progression_manager = ProgressionManager(self.quest_catalog, self.title_catalog)
        self.shop_service = ShopService(self.catalogs, self.merchant_stock)
        self._bind_managers()
        self.running = True

    def _bind_managers(self) -> None:
        self.inventory_manager.bind(self.party, self.inventory)
        self.inventory_manager.selected_member_index = self.selected_member_index
        self.progression_manager.bind(self.party, self.inventory, self.progression)
        self.shop_service.bind(self.party, self.inventory_manager, self.merchant_stock)

    def _item_from_stock(self, item_id: str | None) -> object | None:
        # Convertit un id du stock sauvegardé en objet affichable/équipable.
        entry = self.catalogs.resolve_item(item_id)
        if entry is None:
            return None
        return SimpleNamespace(**entry)

    def run(self) -> None:
        while self.running:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.state == "main_menu":
            self._handle_buttons(position, self.main_menu_screen.buttons())
        elif self.state == "exploration":
            self._handle_buttons(position, self.exploration_screen.buttons())
        elif self.state == "regions":
            self._handle_buttons(position, self.regions_screen.buttons(self))
        elif self.state == "zones":
            self._handle_buttons(position, self.zones_screen.buttons(self))
        elif self.state == "status":
            self.status_screen.handle_click(self, position)
        elif self.state == "battle":
            self.battle_screen.handle_click(self, position)
        elif self.state == "shop":
            self._handle_buttons(position, self.shop_screen.buttons(self))
        elif self.state == "quests":
            self._handle_buttons(position, self.quests_screen.buttons(self))
        elif self.state == "titles":
            self._handle_buttons(position, self.titles_screen.buttons())
        elif self.state == "game_over":
            self._handle_buttons(position, self.game_over_screen.buttons())

    def _handle_buttons(self, position: tuple[int, int], buttons: list[Button]) -> None:
        for button in buttons:
            if button.enabled and button.rect.collidepoint(position):
                self._activate_button(button.action, button.payload)

    def _activate_button(self, action: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        if action == "new_game":
            self._new_game()
        elif action == "load_game":
            self._load_game()
        elif action == "save":
            self._save_game()
        elif action == "encounter":
            self._start_battle()
        elif action == "regions":
            self.state = "regions"
        elif action.startswith("select_region:"):
            region_id = action.split(":", 1)[1]
            if region_id in self.region_catalog:
                self.selected_region_id = region_id
                self.state = "zones"
        elif action.startswith("zone:"):
            zone_id = action.split(":", 1)[1]
            if self.catalogs.zone_belongs_to_region(self.selected_region_id, zone_id):
                self.location = zone_id
                self.state = "exploration"
                self.status_feedback = ""
        elif action.startswith("region:"):
            # Compatibilité avec les anciennes actions de navigation.
            region_id = action.split(":", 1)[1]
            if region_id in self.region_catalog:
                self.location = region_id
                self.status_feedback = ""
        elif action == "shop":
            self.state = "shop"
            self.selected_merchant_id = None
            self.status_feedback = ""
        elif action.startswith("merchant:"):
            self.selected_merchant_id = action.split(":", 1)[1]
            self.status_feedback = ""
        elif action == "merchant_list":
            self.selected_merchant_id = None
            self.status_feedback = ""
        elif action.startswith("buy:"):
            category, item_id = action.split(":", 2)[1:]
            self.status_feedback = self.shop_service.buy(self.selected_merchant_id, category, item_id)
        elif action == "quests":
            self.state = "quests"
        elif action == "titles":
            self.state = "titles"
        elif action.startswith("accept_quest:"):
            quest_id = action.split(":", 1)[1]
            if quest_id not in self.progression["quests"]["active"]:
                self.progression["quests"]["active"].append(quest_id)
        elif action.startswith("claim_quest:"):
            feedback = self.progression_manager.claim_quest(action.split(":", 1)[1])
            if feedback is not None:
                self.status_feedback = feedback
        elif action == "status":
            self.state = "status"
        elif action == "back":
            self.state = "exploration"
        elif action == "quit":
            self._save_game()
            self.running = False
        elif action == "menu":
            self.state = "main_menu"
            self.battle = None
        elif action == "battle_menu":
            self._collect_battle_loot()
            self.state = "exploration"
            self.battle = None
        elif action == "continue":
            if self.battle is not None and self.battle.result == "victory":
                self._collect_battle_loot()
                self.progression["stats"]["victories"] = int(self.progression["stats"].get("victories", 0)) + 1
                self.progression["stats"]["gold_earned"] = int(self.progression["stats"].get("gold_earned", 0)) + sum(enemy.gold_reward for enemy in self.battle.enemies)
                feedback = self.progression_manager.update_titles()
                if feedback is not None:
                    self.status_feedback = feedback
                self._start_battle()
            else:
                self.state = "game_over"
                self.battle = None
        elif action == "flee":
            if self.battle is not None:
                self.battle.flee()
            self.state = "exploration"
        elif action == "use_item":
            item_id = payload.get("item_id")
            if isinstance(item_id, str) and self.battle is not None:
                item = self.catalogs.resolve_item(item_id)
                if item is not None:
                    feedback = self.inventory_manager.use_item(item, self.party.leader if self.party else None)
                    if feedback is not None:
                        self.status_feedback = feedback
                    if feedback is not None and feedback.startswith(item.get("name", item_id)):
                        self.battle.finish_player_action()
        elif action == "select_attack":
            self.selected_battle_action = "attack"
            self.selected_battle_skill_id = None
        elif action == "select_skill":
            skill_id = payload.get("skill_id")
            if self.battle is None or not isinstance(skill_id, str):
                return
            skill = next(
                (item for item in self.battle.available_skills(self.battle.current_actor) if item.id == skill_id),
                None,
            )
            if skill is None:
                return
            if getattr(skill, "target", "single_enemy") != "single_enemy":
                self.battle.player_skill(skill_id)
                self.selected_battle_action = "attack"
                self.selected_battle_skill_id = None
            else:
                self.selected_battle_action = "skill"
                self.selected_battle_skill_id = skill_id

    def _new_game(self) -> None:
        self.core.new_game()
        self.party = self.core.party
        self.location = self.core.location
        self.selected_region_id = "greenlands"
        self.inventory = self.core.inventory
        self.progression = self.core.progression
        self.merchant_stock = self.catalogs.merchant_stock()
        self.selected_merchant_id = None
        self.selected_member_index = 0
        self._bind_managers()
        feedback = self.progression_manager.update_titles()
        if feedback is not None:
            self.status_feedback = feedback
        self.battle = None
        self.state = "exploration"

    def _load_game(self) -> None:
        loaded_state = self.core.load_game()
        self.party = self.core.party
        self.location = self.core.location
        self.selected_region_id = self.catalogs.region_for_zone(self.location)
        self.inventory = self.core.inventory
        self.progression = self.core.progression
        self.merchant_stock = self.core.merchant_stock or self.catalogs.merchant_stock()
        self.selected_member_index = 0
        self._bind_managers()
        self.inventory_manager.merge_member_inventories()
        self.battle = None
        self.selected_merchant_id = None
        self.state = "game_over" if loaded_state == GameState.GAME_OVER else "exploration"
        feedback = self.progression_manager.update_titles()
        if feedback is not None:
            self.status_feedback = feedback

    def _save_game(self) -> None:
        if self.party is None:
            return
        if self.battle is not None and self.battle.result == "victory":
            self._collect_battle_loot()
        self.inventory_manager.merge_member_inventories()
        state = GameState.GAME_OVER if self.state == "game_over" else GameState.EXPLORATION
        self.core.save_game(
            self.party,
            self.location,
            self.inventory,
            self.progression,
            state,
            self.merchant_stock,
        )

    def _collect_battle_loot(self) -> None:
        if self.battle is None or self.battle.loot_collected:
            return
        collected: list[str] = []
        for item_id in self.battle.loot:
            item = self.catalogs.resolve_item(item_id)
            if item is None:
                continue
            self.inventory_manager.add_shared_item(item)
            collected.append(str(item.get("name", item_id)))
        self.battle.loot_collected = True
        if collected:
            self.status_feedback = "Butin obtenu : " + ", ".join(collected) + "."

    def _start_battle(self) -> None:
        if self.party is None:
            return
        self.battle = self.encounter_service.start_battle(self.party, self.location)
        self.selected_battle_action = "attack"
        self.selected_battle_skill_id = None
        self.state = "battle"
        self.progression["stats"]["victories"] = int(self.progression["stats"].get("victories", 0))
        if self.battle.result is not None:
            return

    def _draw(self) -> None:
        self._draw_background()
        if self.state == "main_menu":
            self.main_menu_screen.render(self)
        elif self.state == "exploration":
            self.exploration_screen.render(self)
        elif self.state == "regions":
            self.regions_screen.render(self)
        elif self.state == "zones":
            self.zones_screen.render(self)
        elif self.state == "status":
            self.status_screen.render(self)
        elif self.state == "shop":
            self.shop_screen.render(self)
        elif self.state == "quests":
            self.quests_screen.render(self)
        elif self.state == "titles":
            self.titles_screen.render(self)
        elif self.state == "battle":
            self.battle_screen.render(self)
        elif self.state == "game_over":
            self.game_over_screen.render(self)

    def _draw_background(self) -> None:
        self.renderer.draw_background()

    def _draw_panel(self, rect: pygame.Rect, color: tuple[int, int, int] = PANEL) -> None:
        self.renderer.draw_panel(rect, color)

    def _draw_text(self, text: str, position: tuple[int, int], font: pygame.font.Font | None = None, color: tuple[int, int, int] = TEXT) -> None:
        self.renderer.draw_text(text, position, font, color)

    def _draw_centered_text(self, text: str, center: tuple[int, int], font: pygame.font.Font | None = None, color: tuple[int, int, int] = TEXT) -> None:
        self.renderer.draw_centered_text(text, center, font, color)

    def _button_surface(self, button: Button) -> pygame.Surface:
        return self.renderer.button_surface(button)

    def _draw_buttons(self, buttons: list[Button]) -> None:
        self.renderer.draw_buttons(buttons)

    def _load_sprite(self, relative_path: str | None, size: tuple[int, int], fallback_label: str) -> pygame.Surface:
        return self.renderer.load_sprite(relative_path, size, fallback_label)

    def _main_hero_sprite(self) -> pygame.Surface:
        # Portrait du Joueur utilisé sur le menu principal et les cartes de combat.
        return self._load_sprite("data/assets/sprites/player/ff_000.png", (240, 240), Player.get_name())

    def _enemy_sprite_path(self) -> str | None:
        if self.battle is None:
            return None
        return self.battle.enemy_sprite_path
