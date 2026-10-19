"""Ecran de tentative d'extraction d'une ombre."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, DANGER, MUTED, PANEL, SUCCESS, TEXT
from ui.widgets import Button


class ExtractionScreen:
    def buttons(self, app: Any) -> list[Button]:
        if app._current_extraction() is None:
            return []
        return [
            Button("Lève-toi", pygame.Rect(470, 570, 250, 52), "extract_attempt"),
            Button("Passer", pygame.Rect(750, 570, 150, 52), "extract_skip"),
        ]

    def render(self, app: Any) -> None:
        current = app._current_extraction()
        if current is None:
            app.state = "exploration"
            return
        meta = current["meta"]
        app._draw_panel(pygame.Rect(250, 50, 780, 610), PANEL)
        app._draw_text("Extraction d'ombre", (310, 90), app.font_big, ACCENT)
        app._draw_centered_text(str(meta.get("name", current["id"])), (640, 155), app.font, TEXT)
        sprite = app._load_sprite(meta.get("sprite"), (180, 180), "Ennemi")
        gray = pygame.Surface(sprite.get_size(), pygame.SRCALPHA)
        gray.fill((105, 105, 105, 165))
        sprite.blit(gray, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        app.screen.blit(sprite, sprite.get_rect(center=(640, 300)))
        chance = app._extraction_chance_for_current()
        app._draw_centered_text(f"Chance de réussite : {chance}%", (640, 440), app.font, ACCENT)
        for index in range(3):
            color = ACCENT if index < app.extraction_attempts else MUTED
            pygame.draw.circle(app.screen, color, (570 + index * 70, 500), 18)
            pygame.draw.circle(app.screen, (93, 54, 34), (570 + index * 70, 500), 18, 2)
        app._draw_centered_text(f"Tentatives restantes : {app.extraction_attempts}", (640, 540), app.font_small, MUTED)
        app._draw_buttons(self.buttons(app))

    def handle_click(self, app: Any, position: tuple[int, int]) -> None:
        app._handle_buttons(position, self.buttons(app))
