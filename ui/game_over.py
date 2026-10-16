"""Ecran de reprise apres une defaite."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, DANGER, MUTED, TEXT
from ui.widgets import Button


class GameOverScreen:
    """Explique la pénalité appliquée après la défaite."""

    @staticmethod
    def buttons() -> list[Button]:
        return [Button("Reprendre l'aventure", pygame.Rect(475, 455, 330, 56), "resume_after_defeat")]

    def render(self, app: Any) -> None:
        summary = getattr(app, "defeat_summary", {})
        xp_lost = int(summary.get("xp_lost", 0))
        loss_percent = int(summary.get("xp_loss_percent", 10))
        app._draw_panel(pygame.Rect(250, 135, 780, 410), (31, 24, 35))
        app._draw_centered_text("Défaite", (640, 220), app.font_huge, DANGER)
        app._draw_centered_text(
            f"Tu perds {loss_percent} % de ta progression XP du niveau.",
            (640, 305),
            app.font,
            TEXT,
        )
        app._draw_centered_text(f"XP perdue : {xp_lost}", (640, 350), app.font, ACCENT)
        app._draw_centered_text("Toute la party récupère ses points de vie.", (640, 395), app.font_small, MUTED)
        app._draw_buttons(self.buttons())
