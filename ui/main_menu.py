"""Ecran du menu principal."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL, PANEL_2, TEXT
from ui.widgets import Button


MAIN_HERO_PANEL_POS = (700, 120)
MAIN_HERO_PANEL_SIZE = (460, 470)
MAIN_HERO_SPRITE_POS = (810, 290)


class MainMenuScreen:
    """Construit le rendu du menu principal depuis l'etat de l'application."""

    @staticmethod
    def buttons() -> list[Button]:
        return [
            Button("Nouvelle partie", pygame.Rect(180, 400, 280, 60), "new_game", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Charger", pygame.Rect(180, 475, 280, 60), "load_game", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Quitter", pygame.Rect(180, 550, 280, 60), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(60, 70, 520, 590), PANEL)
        app._draw_text("Python RPG", (130, 225), app.font_huge, ACCENT)
        app._draw_text("<PLACE HOLDER>", (130, 300), app.font, TEXT)
        app._draw_text("Interface pygame medievale", (130, 335), app.font_small, MUTED)
        app._draw_buttons(self.buttons())

        hero_panel = app.renderer.panel_surface(
            MAIN_HERO_PANEL_SIZE,
            "freefantasy",
            "ff_007",
            PANEL_2,
        )
        app.screen.blit(hero_panel, MAIN_HERO_PANEL_POS)
        app.screen.blit(app._main_hero_sprite(), MAIN_HERO_SPRITE_POS)
        app._draw_centered_text(
            "Appuie sur Echap pour quitter",
            (930, 563),
            app.font_small,
            MUTED,
        )
