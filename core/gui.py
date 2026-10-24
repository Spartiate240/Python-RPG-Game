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
from core.classes import ClassService
from core.progression import ProgressionManager
from core.shop import ShopService
from core.shadows import can_extract, extraction_chance, attempt_extraction, EXTRACTION_ATTEMPTS, promote_shadow
from core.save_manager import SaveManager
from entities.player import Player
from party.party import Party
from progression.level_manager import LevelManager
from ui.battle import BattleScreen
from ui.exploration import ExplorationScreen
from ui.extraction import ExtractionScreen
from ui.game_over import GameOverScreen
from ui.main_menu import MainMenuScreen
from ui.save_menu import SaveMenuScreen
from ui.quests import QuestsScreen
from ui.regions import RegionsScreen
from ui.renderer import UIRenderer
from ui.shop import ShopScreen
from ui.shadow_rank import ShadowRankScreen
from ui.classes import ClassesScreen
from ui.ceremony import CeremonyScreen
from ui.dialogue import DialogueScreen
from ui.status import StatusScreen
from ui.theme import PANEL, TEXT
from ui.titles import TitlesScreen
from ui.widgets import Button, NotificationToast
from ui.zones import ZonesScreen


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
SCREEN_SIZE = (1280, 720)
DEATH_XP_LOSS_PERCENT = 10

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
        self.save_menu_screen = SaveMenuScreen()
        self.battle_screen = BattleScreen()
        self.exploration_screen = ExplorationScreen()
        self.extraction_screen = ExtractionScreen()
        self.game_over_screen = GameOverScreen()
        self.regions_screen = RegionsScreen()
        self.zones_screen = ZonesScreen()
        self.shop_screen = ShopScreen()
        self.classes_screen = ClassesScreen()
        self.status_screen = StatusScreen()
        self.shadow_rank_screen = ShadowRankScreen()
        self.quests_screen = QuestsScreen()
        self.titles_screen = TitlesScreen()
        self.dialogue_screen = DialogueScreen()
        self.ceremony_screen = CeremonyScreen()
        self.core = Game()
        self.save_manager = SaveManager()
        self.state = "main_menu"
        self.party: Party | None = None
        self.location: str | None = None
        self.selected_region_id: str | None = None
        self.selected_class_id: str | None = None
        self.inventory: dict[str, dict[str, int]] = {"items": {}, "weapons": {}, "armors": {}, "pets": {}}
        self.battle: Battle | None = None
        self.evaluation_quest_id: str | None = None
        self.ceremony: dict[str, Any] | None = None
        self.extraction_queue: list[dict[str, Any]] = []
        self.extraction_index = 0
        self.extraction_attempts = EXTRACTION_ATTEMPTS
        self.defeat_summary: dict[str, int] = {"xp_lost": 0, "xp_loss_percent": DEATH_XP_LOSS_PERCENT}
        self.selected_battle_action = "attack"
        self.selected_battle_skill_id: str | None = None
        # Message court pour confirmer une action d'équipement ou de retrait.
        self.status_feedback = ""
        self.selected_shadow: Any | None = None
        self.notification = NotificationToast()
        # Personnage actuellement sélectionné dans l'écran statut (index dans party.members).
        self.selected_member_index = 0
        self.status_tab = "equipment"
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
        self.current_dialogue: dict[str, Any] | None = None
        self.dialogue_return_state = "exploration"
        self.progression: dict[str, Any] = {
            "stats": {"victories": 0, "gold_earned": 0, "quests_completed": 0},
            "quests": {"active": [], "completed": [], "claimed": []},
            "titles": {},
        }
        self.inventory_manager = InventoryManager(self.pet_catalog)
        self.progression_manager = ProgressionManager(self.quest_catalog, self.title_catalog, self.catalogs.ranks)
        self.shop_service = ShopService(self.catalogs, self.merchant_stock)
        self.class_service = ClassService(self.catalogs.classes, self.quest_catalog)
        self._bind_managers()
        self.running = True

    def _bind_managers(self) -> None:
        self.inventory_manager.bind(self.party, self.inventory)
        self.inventory_manager.selected_member_index = self.selected_member_index
        self.progression_manager.bind(self.party, self.inventory, self.progression)
        self.shop_service.bind(self.party, self.inventory_manager, self.merchant_stock)
        self.class_service.bind(self.party, self.progression)
        for member in self.party.members if self.party else []:
            if member.class_id not in self.catalogs.classes:
                member.class_id = "warrior"
                member.tier = 1
            member.bind_classes(self.catalogs.classes, self.progression)
            member.refresh_stats(preserve_hp_ratio=hasattr(member, "_saved_hp_ratio"))

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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.state == "quests":
                    self.quests_screen.handle_key(self, event.key)
                elif self.state == "save_menu":
                    self.save_menu_screen.handle_key(event)
                    if self.save_menu_screen.submit_requested():
                        self._activate_button("create_named_game")
            elif event.type == pygame.MOUSEWHEEL and self.state == "quests":
                self.quests_screen.scroll(self, -event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.state == "main_menu":
            self._handle_buttons(position, self.main_menu_screen.buttons())
        elif self.state == "save_menu":
            self.save_menu_screen.click(self, position)
        elif self.state == "exploration":
            self._handle_buttons(position, self.exploration_screen.buttons())
        elif self.state == "regions":
            self._handle_buttons(position, self.regions_screen.buttons(self))
        elif self.state == "zones":
            self._handle_buttons(position, self.zones_screen.buttons(self))
        elif self.state == "status":
            self.status_screen.handle_click(self, position)
        elif self.state == "shadow_rank":
            self.shadow_rank_screen.handle_click(self, position)
        elif self.state == "extraction":
            self.extraction_screen.handle_click(self, position)
        elif self.state == "battle":
            self.battle_screen.handle_click(self, position)
        elif self.state == "shop":
            self._handle_buttons(position, self.shop_screen.buttons(self))
        elif self.state == "classes":
            self._handle_buttons(position, self.classes_screen.buttons(self))
        elif self.state == "quests":
            self._handle_buttons(position, self.quests_screen.buttons(self))
        elif self.state == "titles":
            self._handle_buttons(position, self.titles_screen.buttons())
        elif self.state == "dialogue":
            self._handle_buttons(position, self.dialogue_screen.buttons(self))
        elif self.state == "ceremony":
            self._handle_buttons(position, self.ceremony_screen.buttons())
        elif self.state == "game_over":
            self._handle_buttons(position, self.game_over_screen.buttons())

    def _handle_buttons(self, position: tuple[int, int], buttons: list[Button]) -> None:
        for button in buttons:
            if button.enabled and button.rect.collidepoint(position):
                self._activate_button(button.action, button.payload)

    def _activate_button(self, action: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        if action == "new_game":
            self.save_menu_screen.open("create")
            self.state = "save_menu"
        elif action == "load_game":
            self.save_menu_screen.open("load")
            self.state = "save_menu"
        elif action == "new_named_game":
            self.save_menu_screen.open("create")
        elif action == "create_named_game":
            name = self.save_menu_screen.name.strip()
            if name:
                self._new_game(name, self.save_manager.create_path(name))
        elif action == "load_slot":
            path = payload.get("path")
            if isinstance(path, str):
                self._load_game(Path(path))
        elif action == "save_back":
            self.state = "main_menu"
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
            zone = self.catalogs.zone_for_id(zone_id) or {}
            if self.catalogs.zone_belongs_to_region(self.selected_region_id, zone_id) and self.progression_manager.rank_at_least(zone.get("required_rank")):
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
            merchant_id = self.selected_merchant_id
            dialogue_id = "merchant_pet_shop" if merchant_id == "pet_shop" else "merchant_basic"
            self._open_dialogue(dialogue_id, "shop")
        elif action == "merchant_list":
            self.selected_merchant_id = None
            self.status_feedback = ""
        elif action == "classes":
            self.state = "classes"
            self.selected_class_id = self.party.leader.class_id if self.party and self.party.leader else "warrior"
            self.status_feedback = ""
        elif action.startswith("class_view:"):
            class_id = action.split(":", 1)[1]
            if class_id in self.catalogs.classes:
                self.selected_class_id = class_id
                self.status_feedback = ""
        elif action.startswith("choose_node:"):
            self.status_feedback = self.class_service.choose_node(action.split(":", 1)[1])
        elif action.startswith("learn_class:"):
            self.status_feedback = self.class_service.learn(action.split(":", 1)[1])
        elif action.startswith("choose_class:"):
            self.status_feedback = self.class_service.choose(action.split(":", 1)[1])
            if self.status_feedback.startswith("Classe choisie"):
                self.state = "dialogue"
                self._open_dialogue("intro", "exploration")
        elif action.startswith("buy:"):
            category, item_id = action.split(":", 2)[1:]
            self.status_feedback = self.shop_service.buy(self.selected_merchant_id, category, item_id)
        elif action == "quests":
            self.progression_manager.normalize()
            self.state = "quests"
        elif action == "titles":
            self.state = "titles"
        elif action.startswith("accept_quest:"):
            quest_id = action.split(":", 1)[1]
            self.progression_manager.accept_quest(quest_id)
        elif action.startswith("claim_quest:"):
            quest_id = action.split(":", 1)[1]
            was_claimable = self.progression_manager.quest_status(quest_id) == "claimable"
            feedback = self.progression_manager.claim_quest(quest_id)
            if feedback is not None:
                self.status_feedback = feedback
            if was_claimable:
                quest = self.quest_catalog.get(quest_id, {})
                self.notification.show(f"Quête accomplie : {quest.get('name', quest_id)}")
                if self.progression_manager.last_rank_up is not None:
                    rank = self.catalogs.ranks[self.progression_manager.last_rank_up]
                    self.ceremony = {
                        "title": "Cérémonie de promotion",
                        "icon_rank": self.progression_manager.last_rank_up,
                        "message": f"Vous êtes désormais aventurier de rang {rank['name']}",
                    }
                    self.state = "ceremony"
                elif self.progression_manager.last_tier_up is not None:
                    tier_up = self.progression_manager.last_tier_up
                    member = self.party.leader if self.party else None
                    class_data = self.catalogs.classes.get(str(tier_up["class_id"]), {})
                    tiers = class_data.get("tiers", [])
                    old_tier = int(tier_up["old_tier"])
                    new_tier = int(tier_up["new_tier"])
                    old_name = tiers[old_tier - 1].get("name", f"Tier {old_tier}")
                    new_name = tiers[new_tier - 1].get("name", f"Tier {new_tier}")
                    self.ceremony = {
                        "title": "Passage de tier",
                        "icon_rank": str(class_data.get("emblem", "sword")),
                        "message": f"{old_name} devient {new_name}.",
                        "stat_gain": "Les statistiques sont recalculées avec le nouveau multiplicateur.",
                    }
                    self.state = "ceremony"
        elif action == "pass_evaluation":
            quest_id = payload.get("quest_id")
            quest = self.quest_catalog.get(str(quest_id), {})
            enemy_id = quest.get("evaluation_enemy")
            if isinstance(enemy_id, str) and self.party is not None:
                self.evaluation_quest_id = str(quest_id)
                self.battle = self.encounter_service.start_battle_against(self.party, enemy_id)
                self.selected_battle_action = "attack"
                self.selected_battle_skill_id = None
                self.state = "battle"
        elif action == "status":
            self.state = "status"
        elif action == "toggle_shadow":
            if self.party is not None:
                self.party.toggle_shadow_assignment(payload.get("shadow"))
        elif action == "open_shadow_rank":
            self.selected_shadow = payload.get("shadow")
            self.state = "shadow_rank"
        elif action == "shadow_rank_back":
            self.selected_shadow = None
            self.state = "status"
        elif action == "promote_selected_shadow":
            shadow = self.selected_shadow
            if self.party is not None and shadow is not None:
                necromancer = next((member for member in self.party.members if member.class_id == "necromancer"), None)
                if necromancer is not None:
                    success, result = promote_shadow(shadow, necromancer, self.inventory, self.catalogs.shadow_ranks)
                    if success:
                        self.ceremony = {
                            "title": "Ascension d'une ombre",
                            "shadow": shadow,
                            "icon_rank": result,
                            "message": f"{shadow.name} atteint le rang {self.catalogs.shadow_ranks['ranks'][result]['name']}.",
                            "stat_gain": "Ses statistiques sont recalculées avec sa nouvelle aura.",
                        }
                        self.state = "ceremony"
                    else:
                        self.status_feedback = result
        elif action == "invoke_shadow":
            if self.battle is not None:
                self.battle.invoke_shadow(payload.get("shadow"))
        elif action == "extract_attempt":
            self._attempt_extraction()
        elif action == "extract_skip":
            self._next_extraction()
        elif action == "back":
            self.state = "exploration"
        elif action == "ceremony_continue":
            self.ceremony = None
            self.state = "exploration"
        elif action == "dialogue_choice":
            self._handle_dialogue_choice(payload.get("choice"))
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
                self.progression["stats"]["gold_earned"] = int(self.progression["stats"].get("gold_earned", 0)) + self.battle.total_gold
                defeated = self.progression["stats"].setdefault("enemies_defeated", {})
                for enemy_meta in self.battle.enemy_meta:
                    enemy_id = enemy_meta.get("id")
                    if enemy_id:
                        defeated[enemy_id] = int(defeated.get(enemy_id, 0)) + 1
                self._record_class_victory()
                if self._open_extraction_if_available():
                    return
                feedback = self.progression_manager.update_titles()
                if feedback is not None:
                    self.status_feedback = feedback
                for quest in self.quest_catalog.values():
                    if quest.get("evaluation_rank") and self.progression_manager.quest_status(str(quest["id"])) == "available":
                        self.notification.show(f"Évaluation disponible : rang {self.catalogs.ranks[quest['evaluation_rank']]['name']}")
                        break
                if self.evaluation_quest_id is not None:
                    self.notification.show("Évaluation réussie : réclamez votre promotion au tableau des quêtes.")
                    self.evaluation_quest_id = None
                    self.state = "exploration"
                    self.battle = None
                else:
                    self._start_battle()
            else:
                self._handle_defeat()
        elif action == "resume_after_defeat":
            self.state = "exploration"
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
                        if feedback.startswith(item.get("name", item_id)):
                            self.battle.log_message(f"{self.party.leader.name} {feedback.lower()}")
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
            target_type = getattr(skill, "target", "single_enemy")
            if target_type in ("single_enemy", "all_enemies"):
                self.selected_battle_action = "skill"
                self.selected_battle_skill_id = skill_id
            else:
                self.battle.player_skill(skill_id)
                self.selected_battle_action = "attack"
                self.selected_battle_skill_id = None

    def _new_game(self, profile_name: str = "Héros", save_path: Path | None = None) -> None:
        self.core.new_game(profile_name, save_path)
        self.party = self.core.party
        self.location = self.core.location
        self.selected_region_id = "greenlands"
        self.inventory = self.core.inventory
        self.progression = self.core.progression
        self.progression_manager.bind(self.party, self.inventory, self.progression)
        self.progression_manager.normalize()
        self.merchant_stock = self.catalogs.merchant_stock()
        self.selected_merchant_id = None
        self.selected_member_index = 0
        self._bind_managers()
        feedback = self.progression_manager.update_titles()
        if feedback is not None:
            self.status_feedback = feedback
        self.battle = None
        self.evaluation_quest_id = None
        self.ceremony = None
        self.state = "classes"

    def _open_dialogue(self, dialogue_id: str, return_state: str) -> None:
        dialogue = self.catalogs.dialogues.get(dialogue_id)
        if dialogue is None:
            self.state = return_state
            return
        self.current_dialogue = dialogue
        self.dialogue_return_state = return_state
        self.state = "dialogue"

    def _handle_dialogue_choice(self, choice: object) -> None:
        if not isinstance(choice, dict):
            return
        next_id = choice.get("next")
        if isinstance(next_id, str):
            dialogue = self.catalogs.dialogues.get(next_id)
            if dialogue is not None:
                self.current_dialogue = dialogue
                return
        action = choice.get("action")
        if action == "open_shop":
            self.current_dialogue = None
            self.state = "shop"
        else:
            self.current_dialogue = None
            self.state = self.dialogue_return_state

    def _load_game(self, save_path: Path | None = None) -> None:
        loaded_state = self.core.load_game_from(save_path) if save_path is not None else self.core.load_game()
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
        self.evaluation_quest_id = None
        self.ceremony = None
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

    def _record_class_victory(self) -> None:
        leader = self.party.leader if self.party else None
        if leader is None:
            return
        stats = self.progression.setdefault("stats", {})
        equipment_types = [
            self._item_type(getattr(leader, slot, None))
            for slot in ("weapon_primary", "weapon_secondary", "helmet", "chest", "legs", "boots", "arms")
        ]
        for equipment_type in set(filter(None, equipment_types)):
            stats[f"wins_with_{equipment_type}"] = int(stats.get(f"wins_with_{equipment_type}", 0)) + 1
        active_id = leader.class_id
        mastery_xp = self.battle.total_xp if self.battle is not None else 0
        feedback = self.class_service.gain_mastery(mastery_xp)
        if feedback:
            self.status_feedback = feedback

    def _handle_defeat(self) -> None:
        """Applique la pénalité de défaite avant de rendre la main au joueur."""
        leader = self.party.leader if self.party else None
        xp_lost = 0
        if leader is not None:
            xp_lost = LevelManager().remove_xp(leader, DEATH_XP_LOSS_PERCENT)
        if self.party is not None:
            for member in self.party.members:
                member.heal(member.max_hp)
        self.defeat_summary = {
            "xp_lost": xp_lost,
            "xp_loss_percent": DEATH_XP_LOSS_PERCENT,
        }
        self.state = "game_over"
        self.battle = None

    @staticmethod
    def _class_condition_met(leader: Any, condition: dict[str, Any]) -> bool:
        if not condition:
            return False
        if condition.get("armor_type"):
            return any(PygameApp._item_type(getattr(leader, slot, None)) == condition["armor_type"] for slot in ("helmet", "chest", "legs", "boots", "arms"))
        if condition.get("weapon_type"):
            return any(PygameApp._item_type(getattr(leader, slot, None)) == condition["weapon_type"] for slot in ("weapon_primary", "weapon_secondary"))
        return False

    @staticmethod
    def _item_type(item: Any | None) -> str | None:
        if isinstance(item, dict):
            value = item.get("type")
        else:
            value = getattr(item, "type", None)
        return str(value) if value is not None else None

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

    def _open_extraction_if_available(self) -> bool:
        if self.party is None or not can_extract(self.party):
            return False
        owned = {shadow.enemy_id for shadow in self.party.shadows}
        self.extraction_queue = [
            {"id": meta.get("id"), "meta": meta}
            for meta in self.battle.enemy_meta
            if meta.get("extractable")
        ] if self.battle is not None else []
        if not self.extraction_queue:
            return False
        self.extraction_index = 0
        self.extraction_attempts = EXTRACTION_ATTEMPTS
        self.state = "extraction"
        return True

    def _current_extraction(self) -> dict[str, Any] | None:
        if 0 <= self.extraction_index < len(self.extraction_queue):
            return self.extraction_queue[self.extraction_index]
        return None

    def _extraction_chance_for_current(self) -> int:
        current = self._current_extraction()
        necromancer = next((member for member in self.party.members if member.class_id == "necromancer"), None) if self.party else None
        enemy = next((item for item in self.battle.enemies if item.name == current["meta"].get("name")), None) if self.battle else None
        if current is None or necromancer is None or enemy is None:
            return 0
        return extraction_chance(necromancer, enemy, int(current["meta"].get("extraction_difficulty", 50)))

    def _attempt_extraction(self) -> None:
        current = self._current_extraction()
        necromancer = next((member for member in self.party.members if member.class_id == "necromancer"), None) if self.party else None
        enemy = next((item for item in self.battle.enemies if item.name == current["meta"].get("name")), None) if self.battle else None
        if current is None or necromancer is None or enemy is None:
            self._next_extraction()
            return
        self.extraction_attempts -= 1
        if attempt_extraction(necromancer, enemy, int(current["meta"].get("extraction_difficulty", 50))):
            from entities.shadow import Shadow
            existing_shadow = self.party.shadow_for_enemy(current["id"])
            if existing_shadow is not None:
                existing_shadow.gain_xp(max(1, int(enemy.xp_reward)))
                essence = self.catalogs.resolve_item("shadow_essence")
                self.inventory_manager.add_shared_item(essence)
                self.status_feedback = "Doublon converti : +1 essence d'ombre et XP accordée."
                self.notification.show("Extraction en doublon : +1 essence d'ombre")
            else:
                self.party.add_shadow(Shadow.from_enemy_data(current["id"], current["meta"], enemy.level, 0))
                self.status_feedback = "L'ombre s'est levée."
            self._next_extraction()
        elif self.extraction_attempts <= 0:
            self.status_feedback = "L'extraction a échoué."
            self._next_extraction()

    def _next_extraction(self) -> None:
        self.extraction_index += 1
        self.extraction_attempts = EXTRACTION_ATTEMPTS
        if self.extraction_index >= len(self.extraction_queue):
            self.state = "exploration"
            self.battle = None

    def _draw(self) -> None:
        self._draw_background()
        if self.state == "main_menu":
            self.main_menu_screen.render(self)
        elif self.state == "save_menu":
            self.save_menu_screen.render(self)
        elif self.state == "exploration":
            self.exploration_screen.render(self)
        elif self.state == "extraction":
            self.extraction_screen.render(self)
        elif self.state == "regions":
            self.regions_screen.render(self)
        elif self.state == "zones":
            self.zones_screen.render(self)
        elif self.state == "status":
            self.status_screen.render(self)
        elif self.state == "shop":
            self.shop_screen.render(self)
        elif self.state == "classes":
            self.classes_screen.render(self)
        elif self.state == "quests":
            self.quests_screen.render(self)
        elif self.state == "titles":
            self.titles_screen.render(self)
        elif self.state == "dialogue":
            self.dialogue_screen.render(self)
        elif self.state == "battle":
            self.battle_screen.render(self)
        elif self.state == "game_over":
            self.game_over_screen.render(self)
        elif self.state == "ceremony":
            self.ceremony_screen.render(self)
        elif self.state == "shadow_rank":
            self.shadow_rank_screen.render(self)
        self.notification.draw(self)

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
