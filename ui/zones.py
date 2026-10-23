"""Ecran de selection des zones."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL, SUCCESS
from ui.widgets import Button


class ZonesScreen:
    """Construit le rendu des zones d'une region selectionnee."""

    @staticmethod
    def buttons(app: Any) -> list[Button]:
        region = app.region_catalog.get(app.selected_region_id or "", {})
        buttons = [Button("Retour", pygame.Rect(1035, 610, 150, 48), "regions")]
        for index, zone in enumerate(region.get("zones", [])):
            locked = not app.progression_manager.rank_at_least(zone.get("required_rank", "iron"))
            buttons.append(Button(str(zone.get("name", zone["id"])), pygame.Rect(140, 190 + index * 95, 980, 72), f"zone:{zone['id']}", enabled=zone["id"] != app.location and not locked, payload={"ui_icon": 18 + index}))
        return buttons

    def render(self, app: Any) -> None:
        region = app.region_catalog.get(app.selected_region_id or "", {})
        app._draw_panel(pygame.Rect(70, 55, 1140, 610), PANEL)
        app._draw_text(
            str(region.get("name", "Région")),
            (115, 82),
            app.font_big,
            ACCENT,
        )
        app._draw_text(
            str(region.get("description", "Choisis une zone.")),
            (115, 135),
            app.font_small,
            MUTED,
        )
        app._draw_buttons(self.buttons(app))
        for index, zone in enumerate(region.get("zones", [])):
            required_rank = zone.get("required_rank")
            rect = pygame.Rect(140, 190 + index * 95, 980, 72)
            app._draw_text(str(zone.get("description", "")), (220, rect.y + 39), app.font_small, MUTED)
            if zone.get("id") == app.location:
                app._draw_text("POSITION ACTUELLE", (910, rect.y + 17), app.font_small, SUCCESS)
            if required_rank and not app.progression_manager.rank_at_least(required_rank):
                lock = pygame.Rect(rect.x + 24, rect.y + 20, 18, 17)
                pygame.draw.rect(app.screen, MUTED, lock, width=2, border_radius=2)
                pygame.draw.arc(app.screen, MUTED, pygame.Rect(lock.x + 3, lock.y - 11, 12, 16), 0, 3.14, 2)
                rank = app.catalogs.ranks.get(required_rank, {}).get("name", required_rank)
                app._draw_text(f"Rang requis : {rank}", (rect.x + 70, rect.y + 21), app.font_small, MUTED)
