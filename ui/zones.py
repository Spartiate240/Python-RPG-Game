"""Ecran de selection des zones."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL
from ui.widgets import Button


class ZonesScreen:
    """Construit le rendu des zones d'une region selectionnee."""

    @staticmethod
    def buttons(app: Any) -> list[Button]:
        region = app.region_catalog.get(app.selected_region_id or "", {})
        buttons = [Button("Retour", pygame.Rect(1035, 610, 150, 48), "regions")]
        for index, zone in enumerate(region.get("zones", [])):
            buttons.append(Button(str(zone.get("name", zone["id"])), pygame.Rect(140, 190 + index * 90, 980, 62), f"zone:{zone['id']}", enabled=zone["id"] != app.location))
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
