"""Ecran de selection des regions."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL
from ui.widgets import Button


class RegionsScreen:
    """Construit le rendu de la liste des regions."""

    @staticmethod
    def buttons(app: Any) -> list[Button]:
        buttons = [Button("Retour", pygame.Rect(1035, 610, 150, 48), "back")]
        for index, region in enumerate(app.region_catalog.values()):
            buttons.append(Button(str(region.get("name", region["id"])), pygame.Rect(180, 220 + index * 105, 920, 84), f"select_region:{region['id']}", payload={"ui_icon": 16 + index}))
        return buttons

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(70, 55, 1140, 610), PANEL)
        app._draw_text("Régions", (115, 82), app.font_big, ACCENT)
        app._draw_text(
            "Choisis une région pour afficher ses zones et leurs dangers.",
            (115, 135),
            app.font_small,
            MUTED,
        )
        for index, region in enumerate(app.region_catalog.values()):
            y = 220 + index * 105
            app._draw_text(str(region.get("description", "")), (205, y + 52), app.font_small, MUTED)
            app._draw_text(f"{len(region.get('zones', []))} zone(s)", (930, y + 52), app.font_small, ACCENT)
        app._draw_buttons(self.buttons(app))
