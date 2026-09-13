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
            buttons.append(Button(str(region.get("name", region["id"])), pygame.Rect(140, 190 + index * 90, 980, 62), f"select_region:{region['id']}"))
        return buttons

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(70, 55, 1140, 610), PANEL)
        app._draw_text("Régions", (115, 82), app.font_big, ACCENT)
        app._draw_text(
            "Choisis une région pour afficher ses zones.",
            (115, 135),
            app.font_small,
            MUTED,
        )
        app._draw_buttons(self.buttons(app))
