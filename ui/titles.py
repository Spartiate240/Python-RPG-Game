"""Ecran des titres."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL, SUCCESS, TEXT
from ui.widgets import Button


TITLES_PANEL_RECT = pygame.Rect(70, 55, 1140, 610)
TITLES_BACK_BUTTON_RECT = pygame.Rect(1035, 610, 150, 48)


class TitlesScreen:
    """Construit le rendu de la liste des titres."""

    @staticmethod
    def buttons() -> list[Button]:
        return [Button("Retour", TITLES_BACK_BUTTON_RECT, "back")]

    def render(self, app: Any) -> None:
        feedback = app.progression_manager.update_titles()
        if feedback is not None:
            app.status_feedback = feedback
        app._draw_panel(TITLES_PANEL_RECT, PANEL)
        app._draw_text("Titres", (115, 82), app.font_big, ACCENT)
        app._draw_text(
            "Toutes les distinctions connues et leur avancement",
            (115, 135),
            app.font_small,
            MUTED,
        )
        for index, title in enumerate(app.title_catalog.values()):
            y = 180 + index * 72
            state = app.progression["titles"].get(str(title["id"]), {})
            progress = " / ".join(
                f"{item['current']}/{item['target']}"
                for item in state.get("progress", [])
            )
            unlocked = "Débloqué" if state.get("unlocked") else progress
            app._draw_text(
                str(title.get("name", title["id"])),
                (140, y),
                app.font,
                SUCCESS if state.get("unlocked") else ACCENT,
            )
            app._draw_text(
                f"{title.get('description', '')} — {unlocked}",
                (140, y + 30),
                app.font_small,
                TEXT,
            )
        app._draw_buttons(self.buttons())
