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
