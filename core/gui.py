"""
core/gui.py

Interface pygame du jeu. Elle réutilise les modèles existants
pour la sauvegarde et le combat.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pygame

from core.battle import Battle
from core.catalog import Catalogs
from core.game import Game, GameState
from core.inventory import InventoryManager
from core.progression import ProgressionManager
from entities.combatant import Combatant
from entities.enemy import Enemy
from entities.player import Player
from party.party import Party


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
UI_DIR = DATA_DIR / "assets" / "sprites" / "UI"
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


# LAYOUT SPRITE DU HÉROS (menu principal)
# Ce sont les DEUX SEULES valeurs à changer pour déplacer le sprite du héros
# affiché sur l'écran titre. MAIN_HERO_SPRITE_POS = coin haut-gauche du sprite.
# Diminuer le Y le monte, l'augmenter le descend (même logique pour X: gauche/droite).
MAIN_HERO_PANEL_POS = (700, 120)      # position du cadre décoratif derrière le sprite
MAIN_HERO_PANEL_SIZE = (460, 470)     # taille du cadre décoratif
MAIN_HERO_SPRITE_POS = (810, 290)     # <- MODIFIE CETTE LIGNE pour déplacer le sprite

# Palette volontairement plus "fantasy" que l'UI bleue initiale.
# Chaque couleur est pensée pour rappeler le bois, le cuir, le parchemin,
# Couleurs RGB de "base"
BG = (22, 14, 10)               # Background principal
BG_2 = (49, 31, 19)             # Background secondaire
PANEL = (55, 35, 20)            # Panneaux principaux
PANEL_2 = (74, 49, 29)          # Panneaux secondaires
TEXT = (244, 232, 209)          # Texte principal
MUTED = (184, 165, 139)         # Texte secondaire
ACCENT = (214, 171, 92)         # Accent principal
ACCENT_2 = (121, 154, 102)      # Accent secondaire
SUCCESS = (116, 193, 110)       # Succès
DANGER = (196, 88, 88)          # Danger


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    sprite_theme: str | None = None
    sprite_id: str | None = None


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
        self.catalogs = Catalogs(DATA_DIR)
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
        self._bind_managers()
        self.running = True

    def _bind_managers(self) -> None:
        self.inventory_manager.bind(self.party, self.inventory)
        self.inventory_manager.selected_member_index = self.selected_member_index
        self.progression_manager.bind(self.party, self.inventory, self.progression)

    def _selected_merchant(self) -> dict[str, Any] | None:
        if self.selected_merchant_id is None:
            return None
        return self.merchant_catalog.get(self.selected_merchant_id)

    def _merchant_item_buttons(self) -> list[Button]:
        merchant = self._selected_merchant()
        if merchant is None:
            return []

        buttons: list[Button] = []
        row_index = 0
        stock = self.merchant_stock.get(self.selected_merchant_id or "", {})
        for category, entries in stock.items():
            for item_id, values in entries.items():
                item = self.catalogs.resolve_item(item_id)
                quantity = int(values.get("quantity", 0))
                cost = int(values.get("cost", 0))
                label = item.get("name", item_id) if item else f"Objet inconnu ({item_id})"
                buttons.append(
                    Button(
                        f"{label}  —  {cost} or  —  x{quantity}",
                        pygame.Rect(SHOP_ITEM_BUTTON_X, SHOP_ITEM_START_Y + row_index * SHOP_ITEM_ROW_GAP, SHOP_ITEM_BUTTON_W, SHOP_ITEM_BUTTON_H),
                        f"buy:{category}:{item_id}",
                        payload={"item": item, "category": category, "item_id": item_id, "cost": cost},
                        enabled=item is not None and quantity > 0,
                    )
                )
                row_index += 1
        return buttons

    def _buy_merchant_item(self, parts: list[str]) -> None:
        if len(parts) != 2 or self.selected_merchant_id is None:
            return
        category, item_id = parts
        item = self.catalogs.resolve_item(item_id)
        entry = self.merchant_stock.get(self.selected_merchant_id, {}).get(category, {}).get(item_id)
        leader = self.party.leader if self.party else None
        if item is None or entry is None or leader is None:
            self.status_feedback = "Cet objet n'est pas disponible."
            return
        cost = int(entry.get("cost", 0))
        if int(entry.get("quantity", 0)) <= 0:
            self.status_feedback = "Cet objet est épuisé."
            return
        if not leader.spend_gold(cost):
            self.status_feedback = "Pas assez d'or."
            return

        entry["quantity"] = int(entry["quantity"]) - 1
        self._add_shared_item(SimpleNamespace(**item))
        self.status_feedback = f"{item.get('name', item_id)} acheté."

    def _item_label(self, item: object | None) -> str:
        return self.inventory_manager.item_label(item)

    def _item_slot(self, item: object | None) -> str:
        return self.inventory_manager.item_slot(item)

    def _item_id(self, item: object | None) -> str | None:
        return self.inventory_manager.item_id(item)

    def _item_stat(self, item: object, *names: str) -> object | None:
        return self.inventory_manager.item_stat(item, *names)

    def _item_details(self, item: object) -> list[str]:
        return self.inventory_manager.item_details(item)

    def _item_sprite_path(self, item: object | None) -> str | None:
        # Priorité au sprite déclaré dans le JSON, sinon on prend un fallback existant.
        if item is None:
            return None

        if isinstance(item, dict):
            sprite = item.get("sprite")
        else:
            sprite = getattr(item, "sprite", None)

        if sprite:
            path = Path(sprite)
            if not path.is_absolute():
                path = ROOT_DIR / "data" / sprite
            if path.exists():
                return str(path)

        item_id = self._item_id(item)
        slot = self._item_slot(item)

        weapon_fallbacks = {
            "iron_sword": ROOT_DIR / "data" / "assets" / "sprites" / "weapons" / "iron_sword.png",
            "fire_staff": ROOT_DIR / "data" / "assets" / "sprites" / "weapons" / "fire_staff.png",
        }
        armor_fallbacks = {
            "leather_armor": ROOT_DIR / "data" / "assets" / "sprites" / "armor" / "fa1857.png",
            "chainmail_armor": ROOT_DIR / "data" / "assets" / "sprites" / "armor" / "fa1860.png",
            "plate_armor": ROOT_DIR / "data" / "assets" / "sprites" / "armor" / "fa1893.png",
        }

        if slot == "weapon":
            fallback = weapon_fallbacks.get(item_id)
            if fallback is not None and fallback.exists():
                return str(fallback)
            for candidate in weapon_fallbacks.values():
                if candidate.exists():
                    return str(candidate)
        elif slot:
            fallback = armor_fallbacks.get(item_id)
            if fallback is not None and fallback.exists():
                return str(fallback)
            for candidate in armor_fallbacks.values():
                if candidate.exists():
                    return str(candidate)

        return None

    def _item_from_stock(self, item_id: str | None) -> object | None:
        # Convertit un id du stock sauvegardé en objet affichable/équipable.
        entry = self.catalogs.resolve_item(item_id)
        if entry is None:
            return None
        return SimpleNamespace(**entry)

    def _load_item_sprite(self, item: object | None, size: tuple[int, int]) -> pygame.Surface:
        # Icône réduite pour les listes d'équipement et d'inventaire.
        path = self._item_sprite_path(item)
        if path is None:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surface, ACCENT_2, surface.get_rect(), width=2, border_radius=6)
            return surface

        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, size)
        # Même contour que les autres sprites, à une épaisseur plus fine vu la petite taille.
        pygame.draw.rect(image, ACCENT_2, image.get_rect(), width=1, border_radius=6)
        return image

    def _is_weapon(self, item: object | None) -> bool:
        return self.inventory_manager.is_weapon(item)

    def _selected_member(self) -> Combatant | None:
        self.inventory_manager.selected_member_index = self.selected_member_index
        return self.inventory_manager.selected_member()

    def _equip_item(self, item: object | None) -> None:
        self.inventory_manager.selected_member_index = self.selected_member_index
        feedback = self.inventory_manager.equip_item(item)
        if feedback is not None:
            self.status_feedback = feedback

    def _consume_stock_item(self, item: object) -> bool:
        return self.inventory_manager.consume_stock_item(item)

    def _shared_category(self, item: object) -> str:
        return self.inventory_manager.shared_category(item)

    def _add_shared_item(self, item: object | None) -> None:
        self.inventory_manager.add_shared_item(item)

    def _merge_member_inventories(self) -> None:
        self.inventory_manager.merge_member_inventories()

    def _is_equippable(self, item: object) -> bool:
        return self.inventory_manager.is_equippable(item)

    def _is_pet(self, item: object | None) -> bool:
        return self.inventory_manager.is_pet(item)

    def _unequip_slot(self, slot: str) -> None:
        self.inventory_manager.selected_member_index = self.selected_member_index
        feedback = self.inventory_manager.unequip_slot(slot)
        if feedback is not None:
            self.status_feedback = feedback

    def _status_member_buttons(self) -> list[Button]:
        # Colonne gauche de l'écran statut: un bouton par membre du groupe,
        # utilisé pour choisir de quel personnage on affiche l'équipement à droite.
        if self.party is None:
            return []

        buttons: list[Button] = []
        for index, member in enumerate(self.party.members):
            rect = pygame.Rect(STATUS_LEFT_X, STATUS_CONTENT_Y + index * 96, STATUS_COLUMN_W, 84)
            buttons.append(
                Button(
                    member.name,
                    rect,
                    f"select_member:{index}",
                    payload={"index": index},
                )
            )
        return buttons

    def _status_equipped_buttons(self) -> list[Button]:
        # Colonne droite de l'écran statut: les emplacements actuellement portés
        # par le personnage sélectionné à gauche. Cliquer dessus les retire.
        player = self._selected_member()
        if player is None:
            return []

        slots = [
            ("weapon_primary", "Arme 1", player.weapon_primary),
            ("weapon_secondary", "Arme 2", player.weapon_secondary),
            ("helmet", "Tête", player.helmet),
            ("chest", "Torse", player.chest),
            ("legs", "Jambes", player.legs),
            ("boots", "Pieds", player.boots),
            ("arms", "Bras", player.arms),
            ("pet", "Pet", player.pet),
        ]

        buttons: list[Button] = []
        for index, (slot, label, item) in enumerate(slots):
            box_x = STATUS_RIGHT_X + index * (STATUS_EQUIPPED_BOX_SIZE + STATUS_EQUIPPED_GAP)
            buttons.append(
                Button(
                    label if item is None else "",
                    pygame.Rect(box_x, STATUS_EQUIPPED_Y, STATUS_EQUIPPED_BOX_SIZE, STATUS_EQUIPPED_BOX_SIZE),
                    f"unequip:{slot}",
                    payload={"slot": slot, "item": item, "kind": "equipped", "slot_label": label},
                    enabled=item is not None,
                )
            )
        return buttons

    def _draw_status_equipped_tooltip(self) -> None:
        mouse_position = pygame.mouse.get_pos()
        hovered = next(
            (button for button in self._status_equipped_buttons() if button.enabled and button.rect.collidepoint(mouse_position)),
            None,
        )
        if hovered is None:
            return

        item = hovered.payload.get("item")
        if item is None:
            return

        lines = [self._item_label(item), *self._item_details(item)]
        tooltip_width = 245
        tooltip_height = 18 + len(lines) * 24
        tooltip_x = min(mouse_position[0] + 16, SCREEN_SIZE[0] - tooltip_width - 20)
        tooltip_y = min(mouse_position[1] + 16, SCREEN_SIZE[1] - tooltip_height - 20)
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        self._draw_panel(tooltip_rect, (44, 29, 18))
        for index, line in enumerate(lines):
            self._draw_text(line, (tooltip_rect.x + 12, tooltip_rect.y + 8 + index * 24), self.font_small, ACCENT if index == 0 else TEXT)

    def _status_inventory_buttons(self) -> list[Button]:
        # Colonne droite de l'écran statut: l'inventaire commun du groupe.
        player = self._selected_member()
        if player is None:
            return []

        buttons: list[Button] = []
        row_index = 0

        for category in ("weapons", "armors", "pets", "items"):
            entries = self.inventory.get(category, {})
            for item_id, quantity in entries.items():
                item = self._item_from_stock(item_id)
                if item is None:
                    continue
                row_y = STATUS_INVENTORY_Y + row_index * STATUS_ITEM_ROW_GAP
                buttons.append(
                    Button(
                        f"{self._item_label(item)} x{quantity}",
                        pygame.Rect(STATUS_RIGHT_X, row_y, STATUS_COLUMN_W, 32),
                        f"equip:{item_id}",
                        payload={"item": item, "stock_id": item_id, "category": category, "quantity": quantity, "kind": "shared_inventory"},
                    )
                )
                row_index += 1

        return buttons

    def _handle_status_click(self, position: tuple[int, int]) -> None:
        # Centralise les clics de l'écran statut: retour, sélection de
        # personnage, equip, unequip.
        for button in self._status_buttons():
            if button.rect.collidepoint(position):
                self._activate_button(button.action)
                return

        for button in self._status_member_buttons():
            if button.rect.collidepoint(position):
                self.selected_member_index = int(button.payload["index"])
                self.status_feedback = ""
                return

        for button in self._status_equipped_buttons():
            if button.enabled and button.rect.collidepoint(position):
                slot = str(button.payload.get("slot", button.action.split(":", 1)[1]))
                self._unequip_slot(slot)
                return

        if self._selected_member() is None:
            return

        for button in self._status_inventory_buttons():
            if button.rect.collidepoint(position):
                item = button.payload.get("item")
                if button.payload.get("kind") == "shared_inventory" and item is not None:
                    if not self._is_equippable(item):
                        self.status_feedback = "Cet objet ne peut pas être équipé."
                        return
                    if not self._consume_stock_item(item):
                        self.status_feedback = "Cet objet n'est plus disponible."
                        return
                self._equip_item(item)
                return

    def _load_ui_manifest(self, theme: str) -> list[dict[str, Any]]:
        # Lit la carte des découpes pour une spritesheet donnée.
        # Le manifeste indique où se trouve chaque sprite dans l'image index.
        if theme in self.ui_manifest_cache:
            return self.ui_manifest_cache[theme]

        manifest_path = UI_DIR / theme / "manifest.json"
        if not manifest_path.exists():
            self.ui_manifest_cache[theme] = []
            return []

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.ui_manifest_cache[theme] = manifest
        return manifest

    def _load_ui_sprite(self, theme: str, sprite_id: str, size: tuple[int, int] | None = None) -> pygame.Surface:
        # Premier choix: sprite déjà extrait.
        # Deuxième choix: découpe dans la spritesheet via le manifeste.
        # C'est cette fonction qui relie les ressources UI au rendu final.
        cache_key = (theme, sprite_id, size)
        if cache_key in self.ui_sprite_cache:
            return self.ui_sprite_cache[cache_key]

        extracted_path = UI_DIR / theme / f"{sprite_id}.png"
        if extracted_path.exists():
            sprite = pygame.image.load(str(extracted_path)).convert_alpha()
        else:
            sprite = self._crop_ui_sprite_from_sheet(theme, sprite_id)

        if size is not None and sprite.get_size() != size:
            sprite = pygame.transform.smoothscale(sprite, size)

        self.ui_sprite_cache[cache_key] = sprite
        return sprite

    def _crop_ui_sprite_from_sheet(self, theme: str, sprite_id: str) -> pygame.Surface:
        # Découpe concrète: on lit le manifeste puis on recadre l'image index.
        manifest = self._load_ui_manifest(theme)
        entry = next((item for item in manifest if item.get("id") == sprite_id), None)
        sheet_path = UI_DIR / f"{theme}_index.png"

        if entry is None or not sheet_path.exists():
            # Fallback silencieux pour éviter de casser l'écran si une ressource manque.
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        if theme not in self.ui_sheet_cache:
            self.ui_sheet_cache[theme] = pygame.image.load(str(sheet_path)).convert_alpha()

        sheet = self.ui_sheet_cache[theme]
        rect = pygame.Rect(int(entry["x"]), int(entry["y"]), int(entry["w"]), int(entry["h"]))
        return sheet.subsurface(rect).copy()

    def _ui_panel_surface(self, size: tuple[int, int], theme: str, sprite_id: str, tint: tuple[int, int, int], overlay_theme: str | None = None,
                            overlay_sprite_id: str | None = None, ) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.blit(self._load_ui_sprite(theme, sprite_id, size), (0, 0))
        overlay = pygame.Surface(size, pygame.SRCALPHA)
        overlay.fill((*tint, 115))
        surface.blit(overlay, (0, 0))

        if overlay_sprite_id is not None:
            # 2e sprite dessiné par-dessus la teinte (ex: motif décoratif, emblème).
            surface.blit(
                self._load_ui_sprite(overlay_theme or theme, overlay_sprite_id, size),
                (0, 0),
            )
        return surface

    def _ui_button_surface(self, button: Button, width: int, height: int) -> pygame.Surface:
        theme = button.sprite_theme or "MediavelFree"
        sprite_id = button.sprite_id or ("mf_000" if button.enabled else "ff_006")
        surface = self._ui_panel_surface((width, height), theme, sprite_id, (54, 35, 20))
        outline_color = ACCENT if button.enabled else MUTED
        pygame.draw.rect(surface, outline_color, surface.get_rect(), width=2, border_radius=14)

        if button.payload.get("kind") == "equipped":
            item = button.payload.get("item")
            if item is not None:
                icon_size = (width - 12, height - 12)
                icon = self._load_item_sprite(item, icon_size)
                surface.blit(icon, icon.get_rect(center=surface.get_rect().center))
            else:
                label = self.font_small.render(button.payload.get("slot_label", ""), True, MUTED)
                surface.blit(label, label.get_rect(center=surface.get_rect().center))
            return surface

        item = button.payload.get("item")
        if item is not None and button.action.startswith(("equip", "unequip")):
            # Les boutons de statut ont une icône à gauche et le texte aligné après.
            icon = self._load_item_sprite(item, (24, 24))
            surface.blit(icon, (12, (surface.get_height() - 24) // 2))
            label = self.font_small.render(button.label, True, TEXT if button.enabled else MUTED)
            label_rect = label.get_rect(midleft=(44, surface.get_height() // 2))
            surface.blit(label, label_rect)
            return surface

        label = self.font.render(button.label, True, TEXT if button.enabled else MUTED)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        return surface

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
            self._handle_buttons(position, self._main_menu_buttons())
        elif self.state == "exploration":
            self._handle_buttons(position, self._exploration_buttons())
        elif self.state == "regions":
            self._handle_buttons(position, self._region_buttons())
        elif self.state == "zones":
            self._handle_buttons(position, self._zone_buttons())
        elif self.state == "status":
            self._handle_status_click(position)
        elif self.state == "battle":
            self._handle_battle_click(position)
        elif self.state == "shop":
            self._handle_buttons(position, self._shop_buttons())
        elif self.state == "quests":
            self._handle_buttons(position, self._quest_buttons())
        elif self.state == "titles":
            self._handle_buttons(position, self._title_buttons())
        elif self.state == "game_over":
            self._handle_buttons(position, self._game_over_buttons())

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
            region = self.region_catalog.get(self.selected_region_id or "", {})
            zone_ids = {zone.get("id") for zone in region.get("zones", [])}
            if zone_id in zone_ids:
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
            self._buy_merchant_item(action.split(":", 2)[1:])
        elif action == "quests":
            self.state = "quests"
        elif action == "titles":
            self.state = "titles"
        elif action.startswith("accept_quest:"):
            quest_id = action.split(":", 1)[1]
            if quest_id not in self.progression["quests"]["active"]:
                self.progression["quests"]["active"].append(quest_id)
        elif action.startswith("claim_quest:"):
            self._claim_quest(action.split(":", 1)[1])
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
        elif action == "continue":
            if self.battle is not None and self.battle.result == "victory":
                self.progression["stats"]["victories"] = int(self.progression["stats"].get("victories", 0)) + 1
                self.progression["stats"]["gold_earned"] = int(self.progression["stats"].get("gold_earned", 0)) + sum(enemy.gold_reward for enemy in self.battle.enemies)
                self._update_titles()
                self.state = "exploration"
            else:
                self.state = "game_over"
            self.battle = None
        elif action == "flee":
            if self.battle is not None:
                self.battle.flee()
            self.state = "exploration"
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
        self.party = self.core._new_party()
        self.location = "village"
        self.selected_region_id = "greenlands"
        self.inventory = {"items": {}, "weapons": {}, "armors": {}, "pets": {}}
        self.progression = {
            "stats": {"victories": 0, "gold_earned": 0, "quests_completed": 0},
            "quests": {"active": [], "completed": [], "claimed": []},
            "titles": {},
        }
        self.merchant_stock = self.catalogs.merchant_stock()
        self.selected_merchant_id = None
        self.selected_member_index = 0
        self._bind_managers()
        self.core.progression = self.progression
        self._update_titles()
        self.battle = None
        self.state = "exploration"

    def _load_game(self) -> None:
        self.core.party, loaded_state = self.core._load_progress()
        self.party = self.core.party
        self.location = self.core.location
        self.selected_region_id = self._region_for_zone(self.location)
        self.inventory = self.core.inventory
        self.progression = self.core.progression
        self.selected_member_index = 0
        self._bind_managers()
        self._merge_member_inventories()
        self.battle = None
        self.selected_merchant_id = None
        self.state = "game_over" if loaded_state == GameState.GAME_OVER else "exploration"
        self._update_titles()

    def _save_game(self) -> None:
        if self.party is None:
            return
        self._merge_member_inventories()
        self.core.party = self.party
        self.core.location = self.location
        self.core.inventory = self.inventory
        self.core.progression = self.progression
        self.core.state = GameState.GAME_OVER if self.state == "game_over" else GameState.EXPLORATION
        self.core._save_progress()

    def _start_battle(self) -> None:
        if self.party is None:
            return
        zone = self._zone_for_id(self.location or "village") or {}
        enemy_ids = [
            enemy_id
            for enemy_id in zone.get("enemies", ["goblin"])
            if enemy_id in self.enemy_catalog
        ]
        if not enemy_ids:
            enemy_ids = ["goblin"]
        enemy_id = random.choice(enemy_ids)
        enemy = Enemy.from_id(enemy_id)
        enemy_meta = [self.enemy_catalog.get(enemy_id, {})]
        self.battle = Battle(self.party, [enemy], enemy_meta, self.catalogs.skills)
        self.selected_battle_action = "attack"
        self.selected_battle_skill_id = None
        self.state = "battle"
        self.progression["stats"]["victories"] = int(self.progression["stats"].get("victories", 0))
        if self.battle.result is not None:
            return

    def _draw(self) -> None:
        self._draw_background()
        if self.state == "main_menu":
            self._draw_main_menu()
        elif self.state == "exploration":
            self._draw_exploration()
        elif self.state == "regions":
            self._draw_regions()
        elif self.state == "zones":
            self._draw_zones()
        elif self.state == "status":
            self._draw_status()
        elif self.state == "shop":
            self._draw_shop()
        elif self.state == "quests":
            self._draw_quests()
        elif self.state == "titles":
            self._draw_titles()
        elif self.state == "battle":
            self._draw_battle()
        elif self.state == "game_over":
            self._draw_game_over()

    def _draw_background(self) -> None:
        self.screen.fill(BG)
        pygame.draw.rect(self.screen, BG_2, pygame.Rect(0, SCREEN_SIZE[1] // 2, SCREEN_SIZE[0], SCREEN_SIZE[1] // 2))

    def _draw_panel(self, rect: pygame.Rect, color: tuple[int, int, int] = PANEL) -> None:
        # Fonction centrale pour tous les cadres de l'écran.
        # Elle dessine des zones boisées/parcheminées plutôt que des rectangles plats.
        panel = self._ui_panel_surface(rect.size, "freefantasy", "ff_006", color)
        self.screen.blit(panel, rect.topleft)
        pygame.draw.rect(self.screen, ACCENT_2, rect, width=2, border_radius=18)

    def _draw_text(self, text: str, position: tuple[int, int], font: pygame.font.Font | None = None, color: tuple[int, int, int] = TEXT) -> None:
        font = font or self.font
        self.screen.blit(font.render(text, True, color), position)

    def _draw_centered_text(self, text: str, center: tuple[int, int], font: pygame.font.Font | None = None, color: tuple[int, int, int] = TEXT) -> None:
        font = font or self.font
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=center))

    def _button_surface(self, button: Button) -> pygame.Surface:
        # Tous les boutons passent par ici afin de garder le même style visuel.
        return self._ui_button_surface(button, button.rect.width, button.rect.height)

    def _draw_buttons(self, buttons: list[Button]) -> None:
        for button in buttons:
            self.screen.blit(self._button_surface(button), button.rect.topleft)

    def _load_sprite(self, relative_path: str | None, size: tuple[int, int], fallback_label: str) -> pygame.Surface:
        key = (relative_path or fallback_label, size)
        if key in self.sprite_cache:
            return self.sprite_cache[key]

        surface = pygame.Surface(size, pygame.SRCALPHA)
        if relative_path:
            path = Path(relative_path)
            if not path.is_absolute():
                path = ROOT_DIR / relative_path
            if path.exists():
                image = pygame.image.load(str(path)).convert_alpha()
                image = pygame.transform.smoothscale(image, size)
                # Contour ajouté à chaque sprite pour qu'il se détache du fond.
                pygame.draw.rect(image, ACCENT_2, image.get_rect(), width=2, border_radius=12)
                self.sprite_cache[key] = image
                return image

        surface.fill((51, 65, 85))
        pygame.draw.rect(surface, ACCENT_2, surface.get_rect(), width=2, border_radius=12)
        label = self.font_small.render(fallback_label, True, TEXT)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        self.sprite_cache[key] = surface
        return surface

    def _main_hero_sprite(self) -> pygame.Surface:
        # Portrait du Joueur utilisé sur le menu principal et les cartes de combat.
        return self._load_sprite("data/assets/sprites/player/ff_000.png", (240, 240), Player.get_name())

    def _enemy_sprite_path(self) -> str | None:
        if self.battle is None:
            return None
        return self.battle.enemy_sprite_path

    def _main_menu_buttons(self) -> list[Button]:
        # Colonne gauche du menu principal: trois actions principales.
        return [
            Button("Nouvelle partie", pygame.Rect(180, 400, 280, 60), "new_game", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Charger", pygame.Rect(180, 475, 280, 60), "load_game", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Quitter", pygame.Rect(180, 550, 280, 60), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    def _exploration_buttons(self) -> list[Button]:
        # Colonne gauche de l'écran exploration: actions de progression.
        return [
            Button("Régions", pygame.Rect(800, 200, 320, 48), "regions", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Rencontre", pygame.Rect(800, 255, 320, 48), "encounter", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Boutique", pygame.Rect(800, 309, 320, 48), "shop", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Tableau des quêtes", pygame.Rect(800, 363, 320, 48), "quests", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Titres", pygame.Rect(800, 417, 320, 48), "titles", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("État du groupe", pygame.Rect(800, 471, 320, 48), "status", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder", pygame.Rect(800, 525, 320, 48), "save", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder et quitter", pygame.Rect(800, 579, 320, 48), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    def _region_for_zone(self, zone_id: str | None) -> str | None:
        if zone_id is None:
            return None
        for region_id, region in self.region_catalog.items():
            if any(zone.get("id") == zone_id for zone in region.get("zones", [])):
                return region_id
        return None

    def _zone_for_id(self, zone_id: str) -> dict[str, Any] | None:
        for region in self.region_catalog.values():
            for zone in region.get("zones", []):
                if zone.get("id") == zone_id:
                    return zone
        return None

    def _region_buttons(self) -> list[Button]:
        buttons = [Button("Retour", pygame.Rect(1035, 610, 150, 48), "back")]
        for index, region in enumerate(self.region_catalog.values()):
            buttons.append(
                Button(
                    str(region.get("name", region["id"])),
                    pygame.Rect(140, 190 + index * 90, 980, 62),
                    f"select_region:{region['id']}",
                )
            )
        return buttons

    def _zone_buttons(self) -> list[Button]:
        region = self.region_catalog.get(self.selected_region_id or "", {})
        buttons = [Button("Retour", pygame.Rect(1035, 610, 150, 48), "regions")]
        for index, zone in enumerate(region.get("zones", [])):
            buttons.append(
                Button(
                    str(zone.get("name", zone["id"])),
                    pygame.Rect(140, 190 + index * 90, 980, 62),
                    f"zone:{zone['id']}",
                    enabled=zone["id"] != self.location,
                )
            )
        return buttons

    def _status_buttons(self) -> list[Button]:
        # Petit bouton de retour en bas à droite de l'écran de statut.
        return [Button("Retour", STATUS_BACK_BUTTON_RECT, "back")]

    def _shop_buttons(self) -> list[Button]:
        # La boutique commence par le choix d'un marchand, puis affiche son stock.
        buttons = [Button("Retour", SHOP_BACK_BUTTON_RECT, "back")]
        if self.selected_merchant_id is None:
            for index, merchant in enumerate(self.merchant_catalog.values()):
                buttons.append(
                    Button(
                        str(merchant.get("name", merchant["id"])),
                        pygame.Rect(
                            SHOP_MERCHANT_BUTTON_RECT.x,
                            SHOP_MERCHANT_BUTTON_RECT.y + index * 86,
                            SHOP_MERCHANT_BUTTON_RECT.w,
                            SHOP_MERCHANT_BUTTON_RECT.h,
                        ),
                        f"merchant:{merchant['id']}",
                    )
                )
        else:
            buttons.append(Button("Changer de marchand", pygame.Rect(760, 545, 280, 48), "merchant_list"))
            buttons.extend(self._merchant_item_buttons())
        return buttons

    def _quest_buttons(self) -> list[Button]:
        buttons = [Button("Retour", QUESTS_BACK_BUTTON_RECT, "back")]
        for index, quest in enumerate(self.quest_catalog.values()):
            quest_id = str(quest["id"])
            status = self._quest_status(quest_id)
            if status == "available":
                action = f"accept_quest:{quest_id}"
                label = "Accepter"
            elif status == "claimable":
                action = f"claim_quest:{quest_id}"
                label = "Réclamer"
            else:
                action = "noop"
                label = "Terminé" if status == "claimed" else "En cours"
            buttons.append(Button(label, pygame.Rect(1000, 165 + index * 112, 145, 42), action, enabled=action != "noop"))
        return buttons

    def _title_buttons(self) -> list[Button]:
        return [Button("Retour", TITLES_BACK_BUTTON_RECT, "back")]

    def _condition_progress(self, condition: dict[str, Any]) -> tuple[int, int]:
        return self.progression_manager.condition_progress(condition)

    def _conditions_met(self, conditions: list[dict[str, Any]] | dict[str, Any]) -> bool:
        return self.progression_manager.conditions_met(conditions)

    def _quest_status(self, quest_id: str) -> str:
        return self.progression_manager.quest_status(quest_id)

    def _claim_quest(self, quest_id: str) -> None:
        feedback = self.progression_manager.claim_quest(quest_id)
        if feedback is not None:
            self.status_feedback = feedback

    def _update_titles(self) -> None:
        feedback = self.progression_manager.update_titles()
        if feedback is not None:
            self.status_feedback = feedback

    def _game_over_buttons(self) -> list[Button]:
        # Unique appel à l'action après la défaite: revenir au menu.
        return [Button("Menu principal", pygame.Rect(510, 385, 260, 56), "menu")]

    def _battle_action_buttons(self) -> list[Button]:
        buttons = [
            Button("Attaque normale", pygame.Rect(700, 510, 220, 48), "select_attack", enabled=self.selected_battle_action != "attack"),
        ]
        if self.battle is not None and isinstance(self.battle.current_actor, Player):
            for index, skill in enumerate(self.battle.available_skills(self.battle.current_actor)):
                buttons.append(
                    Button(
                        skill.name,
                        pygame.Rect(700, 565 + index * 48, 220, 42),
                        "select_skill",
                        payload={"skill_id": skill.id},
                        enabled=self.selected_battle_skill_id != skill.id,
                    )
                )
        buttons.append(Button("Fuir", pygame.Rect(950, 580, 190, 50), "flee", sprite_theme="freefantasy", sprite_id="ff_002"))
        return buttons

    def _battle_result_buttons(self) -> list[Button]:
        # Boutons affichés seulement une fois le combat terminé.
        return [
            Button("Continuer", pygame.Rect(890, 550, 240, 56), "continue", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Menu principal", pygame.Rect(890, 605, 240, 40), "menu", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    def _draw_main_menu(self) -> None:
        # Zone 1: colonne gauche avec titre, texte d'accroche et boutons.
        # Zone 2: carte décorative à droite avec le portrait du Joueur.
        self._draw_panel(pygame.Rect(60, 70, 520, 590), PANEL)
        self._draw_text("Python RPG", (130, 225), self.font_huge, ACCENT)
        self._draw_text("<PLACE HOLDER>", (130, 300), self.font, TEXT)
        self._draw_text("Interface pygame médiévale", (130, 335), self.font_small, MUTED)
        self._draw_buttons(self._main_menu_buttons())

        # Le panneau droit sert d'illustration du jeu, comme une affiche d'auberge.
        # Pour déplacer le sprite: modifie MAIN_HERO_SPRITE_POS en haut du fichier.
        hero_panel = self._ui_panel_surface(MAIN_HERO_PANEL_SIZE, "freefantasy", "ff_007", PANEL_2)
        self.screen.blit(hero_panel, MAIN_HERO_PANEL_POS)
        hero = self._main_hero_sprite()
        self.screen.blit(hero, MAIN_HERO_SPRITE_POS)
        self._draw_centered_text("Appuie sur Échap pour quitter", (930, 563), self.font_small, MUTED)

    def _draw_exploration(self) -> None:
        # Exploration = deux panneaux verticaux: infos/actions à gauche, décor à droite.
        self._draw_panel(pygame.Rect(50, 60, 580, 620), PANEL)
        self._draw_panel(pygame.Rect(660, 60, 570, 620), PANEL_2)
        self._draw_text("Exploration", (95, 100), self.font_big, ACCENT)
        self._draw_text("Le groupe avance dans les terres hostiles.", (95, 150), self.font, MUTED)
        zone = self._zone_for_id(self.location or "village") or {}
        region_id = self._region_for_zone(self.location)
        region = self.region_catalog.get(region_id or "", {})
        self._draw_text(f"Région: {region.get('name', 'Inconnue')}", (95, 190), self.font, ACCENT_2)
        self._draw_text(f"Zone: {zone.get('name', self.location or 'Village')}", (95, 225), self.font, ACCENT_2)
        gold = self.party.leader.gold if self.party and self.party.leader else 0
        self._draw_text(f"Or: {gold}", (95, 260), self.font, SUCCESS)
        self._draw_buttons(self._exploration_buttons())
        self._draw_party_summary((125, 270))

        # Panneau droit: plus de sprite "Ennemi" placeholder tant qu'aucun combat
        # n'est en cours (il ne servait qu'à occuper l'espace avant une rencontre).
        self._draw_centered_text("Prêt à explorer", (945, 205), self.font_big, ACCENT_2)
        self._draw_centered_text("Clique sur Rencontre pour lancer un combat.", (945, 250), self.font_small, MUTED)

    def _draw_regions(self) -> None:
        self._draw_panel(pygame.Rect(70, 55, 1140, 610), PANEL)
        self._draw_text("Régions", (115, 82), self.font_big, ACCENT)
        self._draw_text("Choisis une région pour afficher ses zones.", (115, 135), self.font_small, MUTED)
        self._draw_buttons(self._region_buttons())

    def _draw_zones(self) -> None:
        region = self.region_catalog.get(self.selected_region_id or "", {})
        self._draw_panel(pygame.Rect(70, 55, 1140, 610), PANEL)
        self._draw_text(str(region.get("name", "Région")), (115, 82), self.font_big, ACCENT)
        self._draw_text(str(region.get("description", "Choisis une zone.")), (115, 135), self.font_small, MUTED)
        self._draw_buttons(self._zone_buttons())

    def _draw_status(self) -> None:
        # L'écran statut est découpé en trois zones:
        # - le titre et l'aide en haut,
        # - la colonne gauche pour choisir un personnage du groupe,
        # - la colonne droite pour son équipement (porté + inventaire), cliquable.
        self._draw_panel(STATUS_PANEL_RECT, PANEL)
        self._draw_text("État du groupe", (STATUS_LEFT_X, STATUS_TITLE_Y), self.font_big, ACCENT)
        self._draw_text("Clique sur un personnage pour voir son équipement.", (STATUS_LEFT_X, STATUS_HINT_Y), self.font_small, MUTED)
        self._draw_text("Clique sur un emplacement pour retirer, ou un objet pour équiper.", (STATUS_RIGHT_X, STATUS_HINT_Y), self.font_small, MUTED)
        self._draw_status_member_list((STATUS_LEFT_X, STATUS_CONTENT_Y + 30))

        member = self._selected_member()
        member_label = member.name if member is not None else "Aucun personnage"
        self._draw_text(f"Équipement — {member_label}", (STATUS_RIGHT_X, STATUS_CONTENT_Y), self.font, ACCENT)
        self._draw_buttons(self._status_equipped_buttons())
        self._draw_text("Inventaire", (STATUS_RIGHT_X, STATUS_INVENTORY_TITLE_Y), self.font, ACCENT)
        self._draw_buttons(self._status_inventory_buttons())
        self._draw_status_feedback()
        self._draw_status_equipped_tooltip()
        self._draw_buttons(self._status_buttons())

    def _draw_shop(self) -> None:
        self._draw_panel(SHOP_PANEL_RECT, PANEL)
        self._draw_text("Boutique", (100, 110), self.font_big, ACCENT)
        merchant = self._selected_merchant()
        if merchant is None:
            self._draw_text("Choisis ton marchand.", (100, 170), self.font, MUTED)
            for index, merchant_entry in enumerate(self.merchant_catalog.values()):
                self._draw_text(
                    str(merchant_entry.get("description", "")),
                    (175, 282 + index * 86),
                    self.font_small,
                    MUTED,
                )
        else:
            gold = self.party.leader.gold if self.party and self.party.leader else 0
            self._draw_text(str(merchant.get("name", "Marchand")), (100, 165), self.font, ACCENT_2)
            self._draw_text(str(merchant.get("description", "")), (100, 200), self.font_small, MUTED)
            self._draw_text(f"Or: {gold}", (900, 115), self.font, SUCCESS)
            self._draw_text("Stock", (100, 150), self.font, ACCENT)
            self._draw_text("Les références absentes des catalogues sont indisponibles.", (100, 510), self.font_small, MUTED)
            if self.status_feedback:
                self._draw_text(self.status_feedback, (100, 565), self.font_small, TEXT)
        self._draw_buttons(self._shop_buttons())

    def _draw_quests(self) -> None:
        self._draw_panel(QUESTS_PANEL_RECT, PANEL)
        board = self._ui_panel_surface(QUESTS_BOARD_RECT.size, "freefantasy", "ff_001", PANEL_2)
        self.screen.blit(board, QUESTS_BOARD_RECT.topleft)
        self._draw_text("Tableau des quêtes", (115, 82), self.font_big, ACCENT)
        self._draw_text("Les tâches proposées par les habitants du village", (115, 110), self.font_small, MUTED)
        for index, quest in enumerate(self.quest_catalog.values()):
            y = 150 + index * 112
            self._draw_text(str(quest.get("name", quest["id"])), (145, y), self.font, ACCENT)
            self._draw_text(str(quest.get("description", "")), (145, y + 30), self.font_small, TEXT)
            conditions = quest.get("conditions", {})
            conditions = conditions if isinstance(conditions, list) else [conditions]
            progress = ", ".join(
                f"{current}/{target}"
                for current, target in (self._condition_progress(condition) for condition in conditions)
            )
            self._draw_text(f"Avancement: {progress}", (145, y + 56), self.font_small, MUTED)
        self._draw_buttons(self._quest_buttons())

    def _draw_titles(self) -> None:
        self._update_titles()
        self._draw_panel(TITLES_PANEL_RECT, PANEL)
        self._draw_text("Titres", (115, 82), self.font_big, ACCENT)
        self._draw_text("Toutes les distinctions connues et leur avancement", (115, 135), self.font_small, MUTED)
        for index, title in enumerate(self.title_catalog.values()):
            y = 180 + index * 72
            state = self.progression["titles"].get(str(title["id"]), {})
            progress = " / ".join(
                f"{item['current']}/{item['target']}"
                for item in state.get("progress", [])
            )
            unlocked = "Débloqué" if state.get("unlocked") else progress
            self._draw_text(
                str(title.get("name", title["id"])),
                (140, y),
                self.font,
                SUCCESS if state.get("unlocked") else ACCENT,
            )
            self._draw_text(
                f"{title.get('description', '')} — {unlocked}",
                (140, y + 30),
                self.font_small,
                TEXT,
            )
        self._draw_buttons(self._title_buttons())

    def _draw_game_over(self) -> None:
        # Écran de fin, centré et très lisible, avec une seule action de retour.
        self._draw_panel(pygame.Rect(250, 180, 780, 300), (31, 24, 35))
        self._draw_centered_text("GAME OVER", (640, 275), self.font_huge, DANGER)
        self._draw_centered_text("Retourne au menu principal pour recommencer.", (640, 350), self.font, TEXT)
        self._draw_buttons(self._game_over_buttons())

    def _draw_battle(self) -> None:
        if self.battle is None:
            self.state = "exploration"
            return

        # Combat: bandeau titre en haut, cartes cliquables au centre,
        # actions du joueur en bas à droite.
        self._draw_panel(pygame.Rect(50, 60, 1180, 620), PANEL)
        self._draw_text("Combat", (95, 100), self.font_big, ACCENT)
        self._draw_text(self._battle_label(), (95, 150), self.font, MUTED)
        self._draw_battle_cards()

        if self.battle.result is not None:
            self._draw_panel(pygame.Rect(840, 510, 340, 140), PANEL_2)
            self._draw_centered_text(self._battle_label(), (1010, 470), self.font_big, SUCCESS if self.battle.result == "victory" else DANGER)
            self._draw_buttons(self._battle_result_buttons())
            return

        if isinstance(self.battle.current_actor, Player):
            action_label = "une attaque normale" if self.selected_battle_action == "attack" else "le skill sélectionné"
            self._draw_centered_text(f"Sélectionne {action_label}, puis une cible", (940, 480), self.font_small, MUTED)
        self._draw_buttons(self._battle_action_buttons())

    def _battle_label(self) -> str:
        # Texte d'état affiché sous le titre du combat.
        if self.battle is None:
            return ""
        if self.battle.result == "victory":
            return "Victoire"
        if self.battle.result == "defeat":
            return "Défaite"
        if self.battle.result == "flee":
            return "Fuite"
        actor = self.battle.current_actor
        return f"Tour de {getattr(actor, 'name', '...')}"

    def _draw_battle_cards(self) -> None:
        # Le centre de l'écran est réservé aux cartes d'alliés et d'ennemis.
        if self.party is None or self.battle is None:
            return

        allies = [member for member in self.party.active_members() if member.is_alive()]
        hero_sprite = pygame.transform.smoothscale(self._main_hero_sprite(), (80, 80)) # (80, 80) : taille du sprite
        for index, member in enumerate(allies):
            self._draw_actor_card(member, pygame.Rect(90 + index * 180, 275, 160, 160), hero_sprite, (230, 245, 255), sprite_center_y=275 + 85)

        enemy_sprite = self._load_sprite(self._enemy_sprite_path(), (80, 80), "Ennemi")
        for enemy, rect in self._battle_enemy_rects():
            self._draw_actor_card(enemy, rect, enemy_sprite, (255, 220, 220), sprite_center_y=rect.y + 75)
            if isinstance(self.battle.current_actor, Player) and rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(self.screen, ACCENT, rect, width=4, border_radius=18)

    def _battle_enemy_rects(self) -> list[tuple[Enemy, pygame.Rect]]:
        if self.battle is None:
            return []
        enemies = [enemy for enemy in self.battle.enemies if enemy.is_alive()]
        return [
            (enemy, pygame.Rect(90 + index * 220, 455, 160, 160))
            for index, enemy in enumerate(enemies)
        ]

    def _draw_actor_card(
        self, combatant: Combatant, rect: pygame.Rect, sprite: pygame.Surface, tint: tuple[int, int, int],
        sprite_center_y: int | None = None, ) -> None:
        '''
        Dessine une carte de combat pour un allié ou un ennemi.
        pygame.Rect : position et taille de la carte.
        pygame.Surface : sprite du combattant.
        tuple[int, int, int] : teinte de fond pour différencier alliés et ennemis.
        sprite_center_y : position verticale du centre du sprite (optionnel).
        '''
        # Carte standardisée: cadre, sprite, nom, puis barre de PV textuelle.
        self._draw_panel(rect, (23, 33, 52))
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((*tint, 35))
        self.screen.blit(overlay, rect.topleft)

        if sprite_center_y is None:
            # Comportement par défaut : le sprite se colle en haut de la carte,
            # avec une petite marge fixe de 8px, quelle que soit sa taille.
            sprite_center_y = rect.y + sprite.get_height() // 2 + 8

        self.screen.blit(sprite, sprite.get_rect(center=(rect.centerx, sprite_center_y)))
        self._draw_centered_text(combatant.name, (rect.centerx, rect.bottom - 34), self.font_small, TEXT)
        self._draw_centered_text(f"HP {combatant.hp}/{combatant.max_hp}", (rect.centerx, rect.bottom - 14), self.font_small, SUCCESS if combatant.is_alive() else DANGER)

    def _draw_party_summary(self, position: tuple[int, int]) -> None:
        # Sous-écran réutilisé dans exploration et statut.
        # Il affiche une carte par membre du groupe.
        if self.party is None:
            self._draw_text("Aucun groupe.", position, self.font, MUTED)
            return

        x, y = position
        for index, member in enumerate(self.party.members):
            rect = pygame.Rect(x, y + index * 96, 430, 84)
            self._draw_panel(rect, (22, 30, 48))
            sprite = self._load_sprite("data/assets/sprites/player/ff_000.png", (54, 54), "Joueur")
            self.screen.blit(sprite, (rect.x + 14, rect.y + 15))
            self._draw_text(member.name, (rect.x + 82, rect.y + 10), self.font, TEXT)
            self._draw_text(
                f"HP {member.hp}/{member.max_hp}  ATQ {getattr(member, 'total_attack', member.attack)}  DEF {getattr(member, 'total_defense', member.defense)}",
                (rect.x + 82, rect.y + 42),
                self.font_small,
                MUTED,
            )

    def _draw_status_member_list(self, position: tuple[int, int]) -> None:
        # Colonne gauche de l'écran statut: un personnage par ligne, cliquable
        # (voir _status_member_buttons) pour changer l'équipement affiché à droite.
        if self.party is None or not self.party.members:
            self._draw_text("Aucun groupe.", position, self.font, MUTED)
            return

        x, y = position
        for index, member in enumerate(self.party.members):
            rect = pygame.Rect(x, y + index * 96, STATUS_COLUMN_W, 84)
            is_selected = index == self.selected_member_index
            self._draw_panel(rect, PANEL_2 if is_selected else (22, 30, 48))
            sprite = self._load_sprite("data/assets/sprites/player/ff_000.png", (54, 54), "Joueur")
            self.screen.blit(sprite, (rect.x + 14, rect.y + 15))
            self._draw_text(member.name, (rect.x + 82, rect.y + 10), self.font, ACCENT if is_selected else TEXT)
            self._draw_text(
                f"HP {member.hp}/{member.max_hp}  ATQ {getattr(member, 'total_attack', member.attack)}  DEF {getattr(member, 'total_defense', member.defense)}",
                (rect.x + 82, rect.y + 42),
                self.font_small,
                MUTED,
            )

    def _draw_status_feedback(self) -> None:
        # Bandeau bas de page utilisé pour confirmer une action d'équipement.
        # Pour l'aligner ou le recentrer, modifie STATUS_FEEDBACK_RECT.
        if not self.status_feedback:
            return
        self._draw_panel(STATUS_FEEDBACK_RECT, (44, 29, 18))
        self._draw_text(self.status_feedback, (115, 614), self.font_small, TEXT)

    def _handle_battle_click(self, position: tuple[int, int]) -> None:
        # Gestion des clics spécifiques à l'écran combat.
        # 1) si le combat est fini, on clique sur les boutons de fin;
        # 2) sinon, on choisit d'abord l'action, puis sa cible éventuelle.
        if self.battle is None:
            return
        if self.battle.result is not None:
            self._handle_buttons(position, self._battle_result_buttons())
            return

        actor = self.battle.current_actor
        if actor is None or not isinstance(actor, Player):
            return

        for enemy, rect in self._battle_enemy_rects():
            if rect.collidepoint(position):
                if self.selected_battle_action == "attack":
                    self.battle.player_attack(enemy)
                elif self.selected_battle_skill_id is not None:
                    self.battle.player_skill(self.selected_battle_skill_id, enemy)
                self.selected_battle_action = "attack"
                self.selected_battle_skill_id = None
                return

        self._handle_buttons(position, self._battle_action_buttons())