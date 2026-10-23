"""Ecran de l'Inventaire."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, PANEL_2, SUCCESS, TEXT
from ui.widgets import Button
from progression.level_manager import LevelManager


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
STATUS_INVENTORY_TITLE_Y = 314
STATUS_INVENTORY_Y = STATUS_INVENTORY_TITLE_Y + 36
STATUS_FEEDBACK_RECT = pygame.Rect(95, 600, 950, 48)


class StatusScreen:
    """Construit le rendu des statistiques et de l'equipement du groupe."""

    @staticmethod
    def buttons() -> list[Button]:
        return [Button("Retour", pygame.Rect(1075, 610, 130, 56), "back")]

    @staticmethod
    def has_necromancer(app: Any) -> bool:
        return bool(app.party and any(member.class_id == "necromancer" for member in app.party.members))

    @staticmethod
    def army_buttons(app: Any) -> list[Button]:
        if not StatusScreen.has_necromancer(app) or app.party is None:
            return []
        buttons: list[Button] = []
        for index, shadow in enumerate(app.party.shadows):
            x = 180 + (index % 3) * 345
            y = 345 + (index // 3) * 190
            buttons.append(Button(
                f"{shadow.name} {'[active]' if shadow.enemy_id in app.party.assigned_shadow_ids else '[inactive]'}",
                pygame.Rect(x, y, 315, 42),
                "toggle_shadow",
                payload={"shadow": shadow},
                enabled=shadow.enemy_id in app.party.assigned_shadow_ids or len(app.party.assigned_shadow_ids) < app.party.shadow_slots(),
            ))
            buttons.append(Button(
                "Voir la montée de rang",
                pygame.Rect(x + 160, y + 142, 155, 32),
                "open_shadow_rank",
                payload={"shadow": shadow},
            ))
        return buttons

    @staticmethod
    def selected_member(app: Any) -> Any | None:
        app.inventory_manager.selected_member_index = app.selected_member_index
        return app.inventory_manager.selected_member()

    @staticmethod
    def member_buttons(app: Any) -> list[Button]:
        if app.party is None:
            return []
        return [
            Button(
                member.name,
                pygame.Rect(STATUS_LEFT_X, STATUS_CONTENT_Y + index * 96, STATUS_COLUMN_W, 84),
                f"select_member:{index}",
                payload={"index": index},
            )
            for index, member in enumerate(app.party.members)
        ]

    @staticmethod
    def equipped_buttons(app: Any) -> list[Button]:
        player = StatusScreen.selected_member(app)
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
        return [
            Button(
                label if item is None else "",
                pygame.Rect(
                    STATUS_RIGHT_X + index * (STATUS_EQUIPPED_BOX_SIZE + STATUS_EQUIPPED_GAP),
                    STATUS_EQUIPPED_Y,
                    STATUS_EQUIPPED_BOX_SIZE,
                    STATUS_EQUIPPED_BOX_SIZE,
                ),
                f"unequip:{slot}",
                payload={
                    "slot": slot,
                    "item": item,
                    "kind": "equipped",
                    "slot_label": label,
                    "equipment_id": index + 1,
                },
                enabled=item is not None,
            )
            for index, (slot, label, item) in enumerate(slots)
        ]

    @staticmethod
    def inventory_buttons(app: Any) -> list[Button]:
        if StatusScreen.selected_member(app) is None:
            return []
        buttons: list[Button] = []
        row_index = 0
        for category in ("weapons", "armors", "pets", "items"):
            for item_id, quantity in app.inventory.get(category, {}).items():
                item = app._item_from_stock(item_id)
                if item is None:
                    continue
                restriction = app.inventory_manager.equip_restriction_reason(item, StatusScreen.selected_member(app))
                item_label = f"{app.inventory_manager.item_label(item)} x{quantity}"
                if restriction is not None:
                    item_label += f" - {restriction}"
                buttons.append(
                    Button(
                        item_label,
                        pygame.Rect(STATUS_RIGHT_X, STATUS_INVENTORY_Y + row_index * STATUS_ITEM_ROW_GAP, STATUS_COLUMN_W, 32),
                        f"use_item:{item_id}" if category == "items" and app.inventory_manager.item_stat(item, "effect") else f"equip:{item_id}",
                        payload={"item": item, "stock_id": item_id, "category": category, "quantity": quantity, "kind": "shared_inventory"},
                        enabled=restriction is None,
                    )
                )
                row_index += 1
        return buttons

    def draw_member_list(self, app: Any, position: tuple[int, int]) -> None:
        if app.party is None or not app.party.members:
            app._draw_text("Aucun groupe.", position, app.font, MUTED)
            return
        x, y = position
        for index, member in enumerate(app.party.members):
            rect = pygame.Rect(x, y + index * 96, STATUS_COLUMN_W, 84)
            selected = index == app.selected_member_index
            app._draw_panel(rect, PANEL_2 if selected else (22, 30, 48))
            holder = app.renderer.load_asset_sprite("holders", "2", (64, 64))
            app.screen.blit(holder, holder.get_rect(center=(rect.x + 41, rect.y + 42)))
            sprite = app._load_sprite("data/assets/sprites/player/ff_000.png", (54, 54), "Joueur")
            app.screen.blit(sprite, (rect.x + 14, rect.y + 15))
            app._draw_text(member.name, (rect.x + 82, rect.y + 10), app.font, ACCENT if selected else TEXT)
            app._draw_text(f"{member.class_name} - {member.tier_name}", (rect.x + 82, rect.y + 64), app.font_small, ACCENT_2)
            app._draw_text(
                f"HP {member.hp}/{member.max_hp}  ATQ {getattr(member, 'total_attack', member.attack)}  DEF {getattr(member, 'total_defense', member.defense)}",
                (rect.x + 82, rect.y + 42), app.font_small, MUTED,
            )

    def draw_feedback(self, app: Any) -> None:
        if app.status_feedback:
            app._draw_panel(STATUS_FEEDBACK_RECT, (44, 29, 18))
            app._draw_text(app.status_feedback, (115, 614), app.font_small, TEXT)

    def draw_equipped_tooltip(self, app: Any) -> None:
        mouse_position = pygame.mouse.get_pos()
        hovered = next((button for button in self.equipped_buttons(app) if button.enabled and button.rect.collidepoint(mouse_position)), None)
        if hovered is None or hovered.payload.get("item") is None:
            return
        lines = [
            app.inventory_manager.item_label(hovered.payload["item"]),
            *app.inventory_manager.item_details(hovered.payload["item"]),
        ]
        width, height = 245, 18 + len(lines) * 24
        x = min(mouse_position[0] + 16, 1280 - width - 20)
        y = min(mouse_position[1] + 16, 720 - height - 20)
        rect = pygame.Rect(x, y, width, height)
        app._draw_panel(rect, (44, 29, 18))
        for index, line in enumerate(lines):
            app._draw_text(line, (rect.x + 12, rect.y + 8 + index * 24), app.font_small, ACCENT if index == 0 else TEXT)

    def handle_click(self, app: Any, position: tuple[int, int]) -> None:
        if self.has_necromancer(app):
            tab_rect = pygame.Rect(760, 100, 260, 44)
            if tab_rect.collidepoint(position):
                app.status_tab = "army" if app.status_tab != "army" else "equipment"
                return
            if app.status_tab == "army":
                for button in self.army_buttons(app):
                    if button.enabled and button.rect.collidepoint(position):
                        if button.action == "toggle_shadow":
                            app.party.toggle_shadow_assignment(button.payload["shadow"])
                        else:
                            app._activate_button(button.action, button.payload)
                        return
                return
        for button in self.buttons():
            if button.rect.collidepoint(position):
                app._activate_button(button.action)
                return

        for button in self.member_buttons(app):
            if button.rect.collidepoint(position):
                app.selected_member_index = int(button.payload["index"])
                app.status_feedback = ""
                return

        for button in self.equipped_buttons(app):
            if button.enabled and button.rect.collidepoint(position):
                slot = str(button.payload.get("slot", button.action.split(":", 1)[1]))
                app.inventory_manager.selected_member_index = app.selected_member_index
                feedback = app.inventory_manager.unequip_slot(slot)
                if feedback is not None:
                    app.status_feedback = feedback
                return

        if self.selected_member(app) is None:
            return

        for button in self.inventory_buttons(app):
            if button.rect.collidepoint(position):
                item = button.payload.get("item")
                if button.payload.get("kind") == "shared_inventory" and item is not None:
                    if button.action.startswith("use_item:"):
                        app.inventory_manager.selected_member_index = app.selected_member_index
                        feedback = app.inventory_manager.use_item(item, self.selected_member(app))
                        if feedback is not None:
                            app.status_feedback = feedback
                        return
                    if not app.inventory_manager.is_equippable(item):
                        app.status_feedback = "Cet objet ne peut pas être équipé."
                        return
                    restriction = app.inventory_manager.equip_restriction_reason(item, self.selected_member(app))
                    if restriction is not None:
                        app.status_feedback = restriction
                        return
                    if not app.inventory_manager.consume_stock_item(item):
                        app.status_feedback = "Cet objet n'est plus disponible."
                        return
                app.inventory_manager.selected_member_index = app.selected_member_index
                feedback = app.inventory_manager.equip_item(item)
                if feedback is not None:
                    app.status_feedback = feedback
                return

    def render(self, app: Any) -> None:
        app._draw_panel(STATUS_PANEL_RECT, PANEL)
        app._draw_text("Inventaire", (STATUS_LEFT_X, STATUS_TITLE_Y), app.font_big, ACCENT)
        if self.has_necromancer(app):
            tab_rect = pygame.Rect(760, 100, 260, 44)
            app._draw_panel(tab_rect, PANEL_2 if app.status_tab == "army" else (44, 29, 18))
            app._draw_centered_text("Armée des ombres", tab_rect.center, app.font_small, ACCENT)
        if self.has_necromancer(app) and app.status_tab == "army":
            self.render_army(app)
            app._draw_buttons(self.buttons())
            return
        app._draw_text(
            "Clique sur un personnage pour voir son équipement.",
            (STATUS_LEFT_X, STATUS_HINT_Y),
            app.font_small,
            MUTED,
        )
        app._draw_text(
            "Clique sur un emplacement pour retirer, ou un objet pour équiper.",
            (STATUS_RIGHT_X, STATUS_HINT_Y),
            app.font_small,
            MUTED,
        )
        self.draw_member_list(app, (STATUS_LEFT_X, STATUS_CONTENT_Y + 30))

        member = self.selected_member(app)
        member_label = member.name if member is not None else "Aucun personnage"
        app._draw_text(
            f"Équipement — {member_label}",
            (STATUS_RIGHT_X, STATUS_CONTENT_Y),
            app.font,
            ACCENT,
        )
        if member is not None:
            app._draw_text(f"{member.class_name}  {'*' * max(1, int(member.tier))}", (STATUS_RIGHT_X, STATUS_CONTENT_Y + 28), app.font_small, ACCENT_2)
        app._draw_buttons(self.equipped_buttons(app))
        app._draw_text("Inventaire", (STATUS_RIGHT_X, STATUS_INVENTORY_TITLE_Y), app.font, ACCENT)
        app._draw_buttons(self.inventory_buttons(app))
        self.draw_feedback(app)
        self.draw_equipped_tooltip(app)
        app._draw_buttons(self.buttons())

    def render_army(self, app: Any) -> None:
        if app.party is None:
            return
        app._draw_text(f"Cases actives : {len(app.party.assigned_shadow_ids)}/{app.party.shadow_slots()}", (180, 170), app.font, ACCENT)
        for index in range(3):
            unlocked = index < app.party.shadow_slots()
            rect = pygame.Rect(180 + index * 145, 195, 120, 28)
            app._draw_panel(rect, PANEL_2 if unlocked else (35, 25, 20))
            label = "Case libre" if unlocked else f"Tier {index + 2} requis"
            app._draw_centered_text(label, rect.center, app.font_small, TEXT if unlocked else MUTED)
        app._draw_text("Ombres possédées", (180, 315), app.font, ACCENT)
        thresholds = LevelManager().thresholds
        for index, shadow in enumerate(app.party.shadows):
            x = 180 + (index % 3) * 345
            y = 345 + (index // 3) * 190
            rect = pygame.Rect(x, y, 315, 170)
            app._draw_panel(rect, PANEL_2)
            app.screen.blit(app.renderer.shadow_sprite(shadow, (58, 58)), (x + 12, y + 54))
            rank = app.catalogs.shadow_ranks["ranks"].get(shadow.rank_id, {})
            app._draw_text(f"Niv. {shadow.level}", (x + 82, y + 52), app.font_small, TEXT)
            app._draw_text(str(rank.get("name", "Soldat")), (x + 82, y + 78), app.font_small, tuple(rank.get("color", ACCENT)))
            current_threshold = thresholds.get(shadow.level, 0)
            next_threshold = thresholds.get(shadow.level + 1)
            progress = 1.0 if next_threshold is None else max(0.0, min(1.0, (shadow.xp - current_threshold) / max(1, next_threshold - current_threshold)))
            bar = pygame.Rect(x + 82, y + 108, 215, 12)
            pygame.draw.rect(app.screen, (35, 25, 20), bar)
            pygame.draw.rect(app.screen, SUCCESS, pygame.Rect(bar.x, bar.y, int(bar.width * progress), bar.height))
            pygame.draw.rect(app.screen, ACCENT, bar, width=1)
            app._draw_text(f"XP {shadow.xp}", (x + 82, y + 125), app.font_small, MUTED)
            self.draw_shadow_badge(app, (x + 282, y + 72), shadow.rank_id)
        app._draw_buttons(self.army_buttons(app))

    @staticmethod
    def draw_shadow_badge(app: Any, center: tuple[int, int], rank_id: str) -> None:
        color = tuple(app.catalogs.shadow_ranks["ranks"].get(rank_id, {}).get("color", ACCENT))
        x, y = center
        if rank_id == "marshal":
            pygame.draw.polygon(app.screen, color, [(x - 13, y + 8), (x - 10, y - 10), (x, y - 3), (x + 10, y - 10), (x + 13, y + 8)])
        else:
            count = max(1, min(4, list(app.catalogs.shadow_ranks["ranks"]).index(rank_id) + 1))
            for offset in range(count):
                pygame.draw.polygon(app.screen, color, [(x - 16 + offset * 10, y - 4), (x - 11 + offset * 10, y + 5), (x - 6 + offset * 10, y - 4)])
