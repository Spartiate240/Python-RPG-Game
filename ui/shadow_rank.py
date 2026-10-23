"""Panneau de montée de rang des ombres."""

from __future__ import annotations

from typing import Any

import pygame

from core.shadows import next_rank_id, shadow_rank_block_reason, shadow_rank_cost
from ui.theme import ACCENT, DANGER, MUTED, PANEL, SUCCESS, TEXT
from ui.widgets import Button


class ShadowRankScreen:
    def buttons(self, app: Any) -> list[Button]:
        shadow = app.selected_shadow
        if shadow is None:
            return [Button("Retour", pygame.Rect(1075, 610, 130, 56), "back")]
        necromancer = next((member for member in app.party.members if member.class_id == "necromancer"), None)
        reason = shadow_rank_block_reason(shadow, necromancer, app.inventory, app.catalogs.shadow_ranks)
        return [
            Button("Retour", pygame.Rect(1075, 610, 130, 56), "shadow_rank_back"),
            Button(
                "Confirmer la montée" if reason is None else reason,
                pygame.Rect(475, 575, 330, 48),
                "promote_selected_shadow",
                enabled=reason is None,
            ),
        ]

    def handle_click(self, app: Any, position: tuple[int, int]) -> None:
        app._handle_buttons(position, self.buttons(app))

    def render(self, app: Any) -> None:
        shadow = app.selected_shadow
        if shadow is None:
            app.state = "status"
            return
        app._draw_panel(pygame.Rect(180, 55, 920, 610), PANEL)
        app._draw_centered_text("Ascension d'une ombre", (640, 105), app.font_big, ACCENT)
        app.screen.blit(app.renderer.shadow_sprite(shadow, (128, 128)), (576, 135))
        app._draw_centered_text(shadow.name, (640, 285), app.font, TEXT)
        current = app.catalogs.shadow_ranks["ranks"].get(shadow.rank_id, {})
        next_id = next_rank_id(app.catalogs.shadow_ranks, shadow.rank_id)
        next_data = app.catalogs.shadow_ranks["ranks"].get(next_id, {}) if next_id else {}
        app._draw_centered_text(
            f"{current.get('name', shadow.rank_id)}  ->  {next_data.get('name', 'Rang maximal')}",
            (640, 325), app.font, tuple(next_data.get("color", ACCENT)),
        )
        cost = shadow_rank_cost(shadow, app.catalogs.shadow_ranks) or {}
        app._draw_text(f"Niveau de l'ombre : {shadow.level}  (minimum : {cost.get('min_level', '-')})", (330, 380), app.font_small, TEXT)
        app._draw_text("Coûts", (330, 425), app.font, ACCENT)
        rows = [(item_id, int(required)) for item_id, required in cost.get("materials", {}).items()]
        rows.append(("shadow_essence", int(cost.get("shadow_essence", 0))))
        for index, (item_id, required) in enumerate(rows):
            item = app.catalogs.resolve_item(item_id) or {"name": item_id}
            owned = int(app.inventory.get("items", {}).get(item_id, 0))
            color = SUCCESS if owned >= required else DANGER
            app._draw_text(str(item.get("name", item_id)), (360, 465 + index * 30), app.font_small, TEXT)
            app._draw_text(f"{owned} / {required}", (760, 465 + index * 30), app.font_small, color)
        app._draw_buttons(self.buttons(app))