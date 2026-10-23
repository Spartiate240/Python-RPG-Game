"""Rendu des ceremonies generiques de progression."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL, TEXT
from ui.widgets import Button


def draw_rank_badge(app: Any, center: tuple[int, int], rank_id: str, radius: int = 34) -> None:
    color = tuple(app.catalogs.ranks.get(rank_id, {}).get("color", ACCENT))
    x, y = center
    points = [(x, y - radius), (x + radius, y - radius // 2), (x + radius - 5, y + radius // 2), (x, y + radius), (x - radius + 5, y + radius // 2), (x - radius, y - radius // 2)]
    pygame.draw.polygon(app.screen, (47, 30, 19), points)
    inner = [(x, y - radius + 7), (x + radius - 8, y - radius // 2), (x + radius - 12, y + radius // 2 - 3), (x, y + radius - 8), (x - radius + 12, y + radius // 2 - 3), (x - radius + 8, y - radius // 2)]
    pygame.draw.polygon(app.screen, color, inner)
    pygame.draw.polygon(app.screen, ACCENT, points, width=2)


class CeremonyScreen:
    def buttons(self) -> list[Button]:
        return [Button("Continuer", pygame.Rect(490, 565, 300, 54), "ceremony_continue")]

    def render(self, app: Any) -> None:
        overlay = pygame.Surface(app.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((12, 8, 5, 190))
        app.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(250, 95, 780, 540)
        app._draw_panel(rect, PANEL)
        pygame.draw.rect(app.screen, ACCENT, rect, width=4, border_radius=6)
        ceremony = app.ceremony or {}
        app._draw_centered_text(str(ceremony.get("title", "Cérémonie")), (640, 160), app.font_big, ACCENT)
        shadow = ceremony.get("shadow")
        if shadow is not None:
            app.screen.blit(app.renderer.shadow_sprite(shadow, (150, 150)), (565, 220))
            app._draw_centered_text(str(app.catalogs.shadow_ranks["ranks"].get(shadow.rank_id, {}).get("name", shadow.rank_id)), (640, 390), app.font, ACCENT)
        else:
            draw_rank_badge(app, (640, 315), str(ceremony.get("icon_rank", "iron")), 92)
        app._draw_centered_text(str(ceremony.get("message", "Votre progression est reconnue.")), (640, 455), app.font, TEXT)
        if ceremony.get("stat_gain"):
            app._draw_centered_text(str(ceremony["stat_gain"]), (640, 490), app.font_small, TEXT)
        app._draw_centered_text("Le chemin continue.", (640, 525), app.font_small, MUTED)
        app._draw_buttons(self.buttons())