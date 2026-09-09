"""
core/gui.py

Interface pygame du jeu. Elle réutilise les modèles existants
pour la sauvegarde et le combat.
"""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pygame

from core.game import Game, GameState
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


class Battle:
    # Gère uniquement la logique du combat.
    # Elle n'affiche rien et ne connaît pas pygame.
    # Son rôle est de fournir à l'UI l'acteur courant, le journal et le résultat.
    def __init__(self, party: Party, enemies: list[Enemy], enemy_meta: list[dict]) -> None:
        self.party = party
        self.enemies = enemies
        self.enemy_meta = enemy_meta
        self.turn_order: list[Combatant] = []
        self.turn_index = 0
        self.messages: deque[str] = deque(maxlen=7)
        self.result: str | None = None
        self._rebuild_turn_order()
        self._auto_play_until_player()

    def _rebuild_turn_order(self) -> None:
        # Centre logique: tout ce qui combat est fusionné dans une file unique,
        # puis trié par vitesse pour déterminer l'ordre d'affichage des tours.
        combatants = [*self.party.active_members(), *self.enemies]
        self.turn_order = sorted(combatants, key=lambda combatant: combatant.speed, reverse=True)
        self.turn_index = 0

    def _current_actor(self) -> Combatant | None:
        # Le combat affiché à l'écran dépend de cet acteur courant.
        # On saute les morts pour éviter d'afficher un tour vide.
        if self.result is not None:
            return None
        if not self.turn_order:
            self._rebuild_turn_order()
        if not self.turn_order:
            return None
        if self.turn_index >= len(self.turn_order):
            self._rebuild_turn_order()
        if not self.turn_order:
            return None
        while self.turn_index < len(self.turn_order) and not self.turn_order[self.turn_index].is_alive():
            self.turn_index += 1
            if self.turn_index >= len(self.turn_order):
                self._rebuild_turn_order()
                if not self.turn_order:
                    return None
        return self.turn_order[self.turn_index]

    def _advance_turn(self) -> None:
        self.turn_index += 1
        if self.turn_index >= len(self.turn_order):
            self._rebuild_turn_order()

    def _attack_value(self, actor: Combatant) -> int:
        return int(getattr(actor, "total_attack", actor.attack))

    def _defense_value(self, target: Combatant) -> int:
        return int(getattr(target, "total_defense", target.defense))

    def _log(self, message: str) -> None:
        # Le journal visible à droite de l'écran reprend les dernières actions.
        self.messages.append(message)

    def _check_outcome(self) -> None:
        # Cette fonction décide si l'écran de combat doit basculer vers victoire/défaite.
        if not any(member.is_alive() for member in self.party.active_members()):
            self.result = "defeat"
            self._log("Le groupe a été vaincu.")
            return
        if not any(enemy.is_alive() for enemy in self.enemies):
            self.result = "victory"
            total_xp = sum(enemy.xp_reward for enemy in self.enemies)
            total_gold = sum(enemy.gold_reward for enemy in self.enemies)
            for member in self.party.active_members():
                if hasattr(member, "gain_xp"):
                    member.gain_xp(total_xp)
            if self.party.leader is not None:
                self.party.leader.gold += total_gold
            self._log(f"Victoire. +{total_xp} XP, +{total_gold} or.")

    def _sides_for(self, combatant: Combatant) -> tuple[list[Combatant], list[Combatant]]:
        if combatant in self.enemies:
            return self.enemies, list(self.party.active_members())
        return list(self.party.active_members()), self.enemies

    def _resolve_attack(self, actor: Combatant, target: Combatant) -> None:
        # L'UI affiche ce calcul comme un simple message de combat.
        # On garde la règle actuelle: attaque brute moins défense.
        damage = max(1, self._attack_value(actor) - self._defense_value(target))
        dealt = target.take_damage(damage)
        self._log(f"{actor.name} attaque {target.name} pour {dealt} dégâts.")
        self._check_outcome()

    def _auto_play_until_player(self) -> None:
        while self.result is None:
            actor = self._current_actor()
            if actor is None:
                return
            if not actor.is_alive():
                self._advance_turn()
                continue
            if isinstance(actor, Player):
                return

            allies, enemies = self._sides_for(actor)
            action = actor.choose_action(allies, enemies)
            if action.kind == "attack" and action.target is not None:
                self._resolve_attack(actor, action.target)
            elif action.kind == "defend":
                self._log(f"{actor.name} se met en garde.")
            else:
                self._log(f"{actor.name} passe son tour.")
            if self.result is not None:
                return
            self._advance_turn()

    def player_attack(self, target: Combatant) -> None:
        leader = self.party.leader
        if leader is None or not leader.is_alive() or self.result is not None:
            return
        self._resolve_attack(leader, target)
        if self.result is None:
            self._advance_turn()
            self._auto_play_until_player()

    def flee(self) -> None:
        if self.result is None:
            self.result = "flee"
            self._log("Le groupe prend la fuite.")

    @property
    def current_actor(self) -> Combatant | None:
        return self._current_actor()

    @property
    def enemy_sprite_path(self) -> str | None:
        for meta in self.enemy_meta:
            sprite = meta.get("sprite")
            if sprite:
                return str(ROOT_DIR / "data" / sprite)
        return None


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
        self.inventory: dict[str, dict[str, int]] = {"items": {}, "weapons": {}, "armors": {}}
        self.battle: Battle | None = None
        self.pending_targeting = False
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
        self.enemy_catalog = self._load_catalog(DATA_DIR / "enemies.json")
        self.item_catalog = self._load_catalog(DATA_DIR / "items.json")
        self.weapon_catalog = self._load_catalog(DATA_DIR / "weapons.json")
        self.armor_catalog = self._load_catalog(DATA_DIR / "armor.json")
        self.running = True

    def _load_catalog(self, path: Path) -> dict[str, dict]:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return {entry["id"]: entry for entry in data if isinstance(entry, dict) and "id" in entry}

    def _resolve_catalog_item(self, item_id: str | None) -> dict[str, Any] | None:
        # Convertit un identifiant d'objet en entrée JSON complète.
        if item_id is None:
            return None
        return self.item_catalog.get(item_id) or self.weapon_catalog.get(item_id) or self.armor_catalog.get(item_id)

    def _item_label(self, item: object | None) -> str:
        # Nom lisible d'un objet, quel que soit son type concret.
        if item is None:
            return "Aucun"
        if isinstance(item, dict):
            return str(item.get("name", item.get("id", "Inconnu")))
        return str(getattr(item, "name", getattr(item, "id", "Inconnu")))

    def _item_slot(self, item: object | None) -> str:
        # Le slot dit où l'objet peut être porté: weapon, helmet, chest, etc.
        if item is None:
            return ""
        if isinstance(item, dict):
            return str(item.get("slot", ""))
        return str(getattr(item, "slot", ""))

    def _item_id(self, item: object | None) -> str | None:
        if item is None:
            return None
        if isinstance(item, dict):
            return item.get("id")
        return getattr(item, "id", None)

    def _item_stat(self, item: object, *names: str) -> object | None:
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

    def _item_details(self, item: object) -> list[str]:
        details: list[str] = []
        stat_labels = (
            ("ATQ", ("attack_bonus", "damage")),
            ("DEF", ("defense_bonus", "defense")),
            ("PV", ("health", "max_health")),
            ("Vitesse", ("speed",)),
            ("Niveau requis", ("level_required", "required_level")),
            ("Rareté", ("rarity",)),
        )
        for label, names in stat_labels:
            value = self._item_stat(item, *names)
            if value is not None:
                details.append(f"{label}: {value}")
        return details

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
        entry = self._resolve_catalog_item(item_id)
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
        # Les armes de ce projet utilisent le slot "weapon".
        if item is None:
            return False
        if isinstance(item, dict):
            return item.get("slot") == "weapon" or ("damage" in item and not item.get("slot"))
        return getattr(item, "slot", "") == "weapon" or (hasattr(item, "damage") and not getattr(item, "slot", None))

    def _selected_member(self) -> Combatant | None:
        # Personnage actif dans l'écran statut: c'est lui dont on affiche
        # et modifie l'équipement quand on clique sur les colonnes de droite.
        if self.party is None or not self.party.members:
            return None
        if not 0 <= self.selected_member_index < len(self.party.members):
            self.selected_member_index = 0
        return self.party.members[self.selected_member_index]

    def _equip_item(self, item: object | None) -> None:
        # Même règle que dans le menu texte: on retire l'objet en place,
        # on enlève le nouvel objet de l'inventaire, puis on l'équipe.
        player = self._selected_member()
        if player is None or item is None:
            return

        item_id = self._item_id(item)
        if item_id is None:
            return

        if item in player.inventory:
            player.inventory.remove(item)

        slot = self._item_slot(item)

        if self._is_weapon(item):
            if player.weapon is not None:
                player.inventory.append(player.weapon)
            player.equip_weapon(None)
            player.equip_weapon(item)
            self.status_feedback = f"{self._item_label(item)} équipé en arme."
            return

        if slot == "helmet":
            if player.helmet is not None:
                player.inventory.append(player.helmet)
            player.equip_helmet(None)
            player.equip_helmet(item)
        elif slot == "chest":
            if player.chest is not None:
                player.inventory.append(player.chest)
            player.equip_chest(None)
            player.equip_chest(item)
        elif slot == "legs":
            if player.legs is not None:
                player.inventory.append(player.legs)
            player.equip_legs(None)
            player.equip_legs(item)
        elif slot == "boots":
            if player.boots is not None:
                player.inventory.append(player.boots)
            player.equip_boots(None)
            player.equip_boots(item)
        elif slot == "arms":
            if player.arms is not None:
                player.inventory.append(player.arms)
            player.equip_arms(None)
            player.equip_arms(item)
        else:
            self.status_feedback = "Cet objet ne peut pas être équipé."
            return

        self.status_feedback = f"{self._item_label(item)} équipé."

    def _consume_stock_item(self, item: object) -> bool:
        item_id = self._item_id(item)
        if item_id is None:
            return False
        category = "weapons" if self._is_weapon(item) else "armors" if self._item_slot(item) else "items"
        entries = self.inventory.get(category, {})
        quantity = int(entries.get(item_id, 0))
        if quantity <= 0:
            return False
        if quantity == 1:
            del entries[item_id]
        else:
            entries[item_id] = quantity - 1
        return True

    def _is_equippable(self, item: object) -> bool:
        return self._is_weapon(item) or self._item_slot(item) in {
            "helmet", "chest", "legs", "boots", "arms"
        }

    def _unequip_slot(self, slot: str) -> None:
        # Cliquer sur un slot équipé le remet simplement dans l'inventaire
        # du personnage actuellement sélectionné.
        player = self._selected_member()
        if player is None:
            return

        if slot == "weapon" and player.weapon is not None:
            player.inventory.append(player.weapon)
            player.equip_weapon(None)
            self.status_feedback = "Arme retirée."
        elif slot == "helmet" and player.helmet is not None:
            player.inventory.append(player.helmet)
            player.equip_helmet(None)
            self.status_feedback = "Tête retirée."
        elif slot == "chest" and player.chest is not None:
            player.inventory.append(player.chest)
            player.equip_chest(None)
            self.status_feedback = "Torse retiré."
        elif slot == "legs" and player.legs is not None:
            player.inventory.append(player.legs)
            player.equip_legs(None)
            self.status_feedback = "Jambes retirées."
        elif slot == "boots" and player.boots is not None:
            player.inventory.append(player.boots)
            player.equip_boots(None)
            self.status_feedback = "Bottes retirées."
        elif slot == "arms" and player.arms is not None:
            player.inventory.append(player.arms)
            player.equip_arms(None)
            self.status_feedback = "Bras retirés."

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
            ("weapon", "Arme", player.weapon),
            ("helmet", "Tête", player.helmet),
            ("chest", "Torse", player.chest),
            ("legs", "Jambes", player.legs),
            ("boots", "Pieds", player.boots),
            ("arms", "Bras", player.arms),
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
        # Colonne droite de l'écran statut, sous les emplacements équipés:
        # on y fusionne l'inventaire du personnage sélectionné et le stock
        # sauvegardé, pour que les armures et armes non portées restent visibles.
        player = self._selected_member()
        if player is None:
            return []

        buttons: list[Button] = []
        row_index = 0

        for item in player.inventory:
            label = self._item_label(item)
            slot = self._item_slot(item)
            suffix = f" [{slot}]" if slot else ""
            row_y = STATUS_INVENTORY_Y + row_index * STATUS_ITEM_ROW_GAP
            buttons.append(
                Button(
                    f"{label}{suffix}",
                    pygame.Rect(STATUS_RIGHT_X, row_y, STATUS_COLUMN_W, 32),
                    f"equip:{row_index}",
                    payload={"item": item, "index": row_index, "kind": "inventory"},
                    sprite_theme = "freefantasy",
                    sprite_id = "ff_001"
                )
            )
            row_index += 1

        for category in ("weapons", "armors", "items"):
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
                        payload={"item": item, "stock_id": item_id, "category": category, "quantity": quantity, "kind": "stock"},
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
                if button.payload.get("kind") == "stock" and item is not None:
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
        elif self.state == "status":
            self._handle_status_click(position)
        elif self.state == "battle":
            self._handle_battle_click(position)
        elif self.state == "shop":
            self._handle_buttons(position, self._shop_buttons())
        elif self.state == "game_over":
            self._handle_buttons(position, self._game_over_buttons())

    def _handle_buttons(self, position: tuple[int, int], buttons: list[Button]) -> None:
        for button in buttons:
            if button.enabled and button.rect.collidepoint(position):
                self._activate_button(button.action)

    def _activate_button(self, action: str) -> None:
        if action == "new_game":
            self._new_game()
        elif action == "load_game":
            self._load_game()
        elif action == "save":
            self._save_game()
        elif action == "encounter":
            self._start_battle()
        elif action == "shop":
            self.state = "shop"
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
                self.state = "exploration"
            else:
                self.state = "game_over"
            self.battle = None
        elif action == "attack":
            self.pending_targeting = True
        elif action == "flee":
            if self.battle is not None:
                self.battle.flee()
            self.state = "exploration"
            self.pending_targeting = False

    def _handle_battle_click(self, position: tuple[int, int]) -> None:
        if self.battle is None:
            return
        if self.battle.result is not None:
            self._handle_buttons(position, self._battle_result_buttons())
            return
        actor = self.battle.current_actor
        if actor is None or not isinstance(actor, Player):
            return
        if not self.pending_targeting:
            self._handle_buttons(position, self._battle_action_buttons())
            return

        enemies = [enemy for enemy in self.battle.enemies if enemy.is_alive()]
        for index, enemy in enumerate(enemies):
            rect = pygame.Rect(860, 200 + index * 74, 300, 54)
            if rect.collidepoint(position):
                self.battle.player_attack(enemy)
                self.pending_targeting = False
                if self.battle.result is not None:
                    self.state = "battle"
                return

    def _new_game(self) -> None:
        self.party = self.core._new_party()
        self.location = None
        self.inventory = {"items": {}, "weapons": {}, "armors": {}}
        self.battle = None
        self.pending_targeting = False
        self.selected_member_index = 0
        self.state = "exploration"

    def _load_game(self) -> None:
        self.core.party, loaded_state = self.core._load_progress()
        self.party = self.core.party
        self.location = self.core.location
        self.inventory = self.core.inventory
        self.battle = None
        self.pending_targeting = False
        self.selected_member_index = 0
        self.state = "game_over" if loaded_state == GameState.GAME_OVER else "exploration"

    def _save_game(self) -> None:
        if self.party is None:
            return
        self.core.party = self.party
        self.core.location = self.location
        self.core.inventory = self.inventory
        self.core.state = GameState.GAME_OVER if self.state == "game_over" else GameState.EXPLORATION
        self.core._save_progress()

    def _start_battle(self) -> None:
        if self.party is None:
            return
        enemy = Enemy.from_id("goblin")
        enemy_meta = [self.enemy_catalog.get("goblin", {})]
        self.battle = Battle(self.party, [enemy], enemy_meta)
        self.pending_targeting = False
        self.state = "battle"
        if self.battle.result is not None:
            return

    def _draw(self) -> None:
        self._draw_background()
        if self.state == "main_menu":
            self._draw_main_menu()
        elif self.state == "exploration":
            self._draw_exploration()
        elif self.state == "status":
            self._draw_status()
        elif self.state == "shop":
            self._draw_shop()
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
            Button("Rencontre", pygame.Rect(800, 295, 320, 58), "encounter",sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Boutique", pygame.Rect(800, 365, 320, 58), "shop", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("État du groupe", pygame.Rect(800, 435, 320, 58), "status", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder", pygame.Rect(800, 505, 320, 58), "save", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder et quitter", pygame.Rect(800, 575, 320, 58), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    def _status_buttons(self) -> list[Button]:
        # Petit bouton de retour en bas à droite de l'écran de statut.
        return [Button("Retour", STATUS_BACK_BUTTON_RECT, "back")]

    def _shop_buttons(self) -> list[Button]:
        # Bouton de retour de l'écran boutique.
        return [Button("Retour", pygame.Rect(900, 610, 220, 56), "back")]

    def _game_over_buttons(self) -> list[Button]:
        # Unique appel à l'action après la défaite: revenir au menu.
        return [Button("Menu principal", pygame.Rect(510, 385, 260, 56), "menu")]

    def _battle_action_buttons(self) -> list[Button]:
        # Barre d'actions du joueur en bas à droite pendant le combat.
        return [
            Button("Attaquer", pygame.Rect(750, 510, 320, 58), "attack", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Fuir", pygame.Rect(750, 580, 320, 50), "flee", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

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
        gold = self.party.leader.gold if self.party and self.party.leader else 0
        self._draw_text(f"Or: {gold}", (130, 230), self.font, SUCCESS)
        self._draw_buttons(self._exploration_buttons())
        self._draw_party_summary((125, 270))

        # Panneau droit: plus de sprite "Ennemi" placeholder tant qu'aucun combat
        # n'est en cours (il ne servait qu'à occuper l'espace avant une rencontre).
        self._draw_centered_text("Prêt à explorer", (945, 205), self.font_big, ACCENT_2)
        self._draw_centered_text("Clique sur Rencontre pour lancer un combat.", (945, 250), self.font_small, MUTED)

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
        # Écran boutique encore volontairement simple: il sert de place réservée.
        self._draw_panel(pygame.Rect(60, 70, 1160, 580), PANEL)
        self._draw_text("Boutique", (100, 110), self.font_big, ACCENT)
        self._draw_text("Le marchand n'est pas encore branché à l'UI pygame.", (100, 170), self.font, MUTED)
        self._draw_centered_text("Écran réservé", (640, 340), self.font_big, ACCENT_2)
        self._draw_buttons(self._shop_buttons())

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

        # Combat: bandeau titre en haut, cards des combattants au centre,
        # journal à droite, actions du joueur en bas à droite.
        self._draw_panel(pygame.Rect(50, 60, 1180, 620), PANEL)
        self._draw_text("Combat", (95, 100), self.font_big, ACCENT)
        self._draw_text(self._battle_label(), (95, 150), self.font, MUTED)
        self._draw_battle_cards()
        self._draw_battle_log()

        if self.battle.result is not None:
            self._draw_panel(pygame.Rect(840, 510, 340, 140), PANEL_2)
            self._draw_centered_text(self._battle_label(), (1010, 470), self.font_big, SUCCESS if self.battle.result == "victory" else DANGER)
            self._draw_buttons(self._battle_result_buttons())
            return

        if self.pending_targeting:
            self._draw_centered_text("Choisis une cible", (1010, 525), self.font_small, MUTED)
            self._draw_enemy_targets()
        else:
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
        enemies = [enemy for enemy in self.battle.enemies if enemy.is_alive()]

        hero_sprite = pygame.transform.smoothscale(self._main_hero_sprite(), (80, 80)) # (80, 80) : taille du sprite
        for index, member in enumerate(allies):
            self._draw_actor_card(member, pygame.Rect(90 + index * 180, 275, 160, 160), hero_sprite, (230, 245, 255), sprite_center_y=275 + 85)

        enemy_sprite = self._load_sprite(self._enemy_sprite_path(), (80, 80), "Ennemi")
        for index, enemy in enumerate(enemies):
            self._draw_actor_card(enemy, pygame.Rect(90 + index * 220, 455, 160, 160), enemy_sprite, (255, 220, 220), sprite_center_y=455 + 75)

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

    def _draw_battle_log(self) -> None:
        # Colonne droite: historique compact des dernières actions.
        self._draw_panel(pygame.Rect(835, 180, 350, 250), PANEL_2)
        self._draw_text("Journal", (970, 145), self.font, ACCENT)
        if self.battle is None:
            return
        for index, message in enumerate(self.battle.messages):
            self._draw_text(message, (885, 250 + index * 28), self.font_small, TEXT)

    def _draw_enemy_targets(self) -> None:
        # Sous-zone de ciblage à droite du combat, affichée seulement après clic sur "Attaquer".
        if self.battle is None:
            return
        enemies = [enemy for enemy in self.battle.enemies if enemy.is_alive()]
        for index, enemy in enumerate(enemies):
            rect = pygame.Rect(860, 250 + index * 74, 300, 54)
            button = Button(enemy.name, rect, f"target_{index}")
            self.screen.blit(self._button_surface(button), rect.topleft)

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

    def _handle_battle_target_click(self, position: tuple[int, int]) -> None:
        # Gère le clic sur l'une des cibles affichées à droite du combat.
        if self.battle is None:
            return
        enemies = [enemy for enemy in self.battle.enemies if enemy.is_alive()]
        for index, enemy in enumerate(enemies):
            rect = pygame.Rect(860, 220 + index * 74, 300, 54)
            if rect.collidepoint(position):
                self.battle.player_attack(enemy)
                self.pending_targeting = False
                if self.battle.result is None:
                    self.state = "battle"
                return

    def _handle_battle_click(self, position: tuple[int, int]) -> None:
        # Gestion des clics spécifiques à l'écran combat.
        # 1) si le combat est fini, on clique sur les boutons de fin;
        # 2) sinon, soit on choisit une action, soit une cible.
        if self.battle is None:
            return
        if self.battle.result is not None:
            self._handle_buttons(position, self._battle_result_buttons())
            return

        actor = self.battle.current_actor
        if actor is None or not isinstance(actor, Player):
            return

        if self.pending_targeting:
            self._handle_battle_target_click(position)
            return

        self._handle_buttons(position, self._battle_action_buttons())