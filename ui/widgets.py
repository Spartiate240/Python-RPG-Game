"""Composants communs de l'interface pygame."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pygame


@dataclass
class Button:
    """Bouton visuel et action associee."""

    label: str
    rect: pygame.Rect
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    sprite_theme: str | None = None
    sprite_id: str | None = None


class NotificationToast:
    """Notification generique en parchemin, animee depuis le haut."""

    def __init__(self, duration_ms: int = 3500) -> None:
        self.duration_ms = duration_ms
        self.message = ""
        self.started_at = 0

    def show(self, message: str) -> None:
        self.message = message
        self.started_at = pygame.time.get_ticks()

    def draw(self, app: Any) -> None:
        if not self.message:
            return
        elapsed = pygame.time.get_ticks() - self.started_at
        total = self.duration_ms + 700
        if elapsed >= total:
            self.message = ""
            return
        slide = min(1.0, elapsed / 350.0)
        alpha = 255
        if elapsed > self.duration_ms:
            alpha = max(0, int(255 * (1 - (elapsed - self.duration_ms) / 700.0)))
        y = int(-58 + 78 * slide)
        surface = pygame.Surface((620, 58), pygame.SRCALPHA)
        surface.fill((132, 91, 48, alpha))
        pygame.draw.rect(surface, (214, 171, 92, alpha), surface.get_rect(), width=2, border_radius=5)
        text = app.font_small.render(self.message, True, (244, 232, 209))
        surface.blit(text, text.get_rect(center=surface.get_rect().center))
        app.screen.blit(surface, surface.get_rect(midtop=(640, y)))
