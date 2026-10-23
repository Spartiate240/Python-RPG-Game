"""Ecran de dialogue narratif reutilisable."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, PANEL_2, TEXT
from ui.widgets import Button


class DialogueScreen:
    """Affiche une replique et les choix du noeud courant."""

    def buttons(self, app: Any) -> list[Button]:
        dialogue = app.current_dialogue or {}
        choices = dialogue.get("choices", [])
        buttons: list[Button] = []
        for index, choice in enumerate(choices):
            buttons.append(
                Button(
                    str(choice.get("label", "Continuer")),
                    pygame.Rect(145, 455 + index * 62, 990, 48),
                    "dialogue_choice",
                    payload={"choice": choice, "ui_icon": 21 + index},
                )
            )
        return buttons

    @staticmethod
    def _lines(app: Any, text: str, max_width: int) -> list[str]:
        lines: list[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if current and app.font.size(candidate)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def render(self, app: Any) -> None:
        dialogue = app.current_dialogue or {}
        app._draw_panel(pygame.Rect(90, 70, 1100, 590), PANEL)
        portrait = app.renderer.load_asset_sprite("holders", "2", (128, 128))
        app.screen.blit(portrait, portrait.get_rect(topleft=(140, 105)))
        icon = app.renderer.load_asset_sprite("icons", "16", (88, 88))
        app.screen.blit(icon, icon.get_rect(center=(204, 169)))
        app._draw_text(str(dialogue.get("speaker", "")), (300, 125), app.font_big, ACCENT)
        app._draw_text("Dialogue", (302, 175), app.font_small, MUTED)
        app._draw_panel(pygame.Rect(300, 205, 840, 190), PANEL_2)
        for index, line in enumerate(self._lines(app, str(dialogue.get("text", "")), 780)):
            app._draw_text(line, (335, 240 + index * 34), app.font, TEXT)
        app._draw_text("Choisis une réponse", (145, 430), app.font_small, MUTED)
        app._draw_buttons(self.buttons(app))
