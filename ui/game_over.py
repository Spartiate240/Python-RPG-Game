"""Ecran de fin de partie."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import DANGER, TEXT
from ui.widgets import Button


class GameOverScreen:
    """Construit le rendu de la fin de partie."""

    @staticmethod
    def buttons() -> list[Button]:
        return [Button("Menu principal", pygame.Rect(510, 385, 260, 56), "menu")]

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(250, 180, 780, 300), (31, 24, 35))
        app._draw_centered_text("GAME OVER", (640, 275), app.font_huge, DANGER)
        app._draw_centered_text(
            "Retourne au menu principal pour recommencer.",
            (640, 350),
            app.font,
            TEXT,
        )
        app._draw_buttons(self.buttons())
