"""Ecran d'apprentissage des classes."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, SUCCESS, TEXT
from ui.widgets import Button


class ClassesScreen:
    """Affiche les classes et leurs prerequis d'apprentissage."""

    def buttons(self, app: Any) -> list[Button]:
        buttons = [Button("Retour", pygame.Rect(1050, 600, 130, 56), "shop")]
        for index, class_id in enumerate(app.catalogs.classes):
            class_data = app.catalogs.classes[class_id]
            state = app.class_service.state(class_id)
            unlocked = bool(state.get("unlocked")) or bool(class_data.get("default"))
            buttons.append(
                Button(
                    "Apprise" if unlocked else "Apprendre",
                    pygame.Rect(965, 175 + index * 145, 190, 46),
                    f"learn_class:{class_id}",
                    enabled=not unlocked and app.class_service.is_available(class_id),
                )
            )
        return buttons

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(60, 50, 1160, 610), PANEL)
        app._draw_text("Apprentissage des classes", (95, 85), app.font_big, ACCENT)
        app._draw_text("Choisis une voie et remplis ses prérequis.", (95, 135), app.font_small, MUTED)
        for index, class_id in enumerate(app.catalogs.classes):
            class_data = app.catalogs.classes[class_id]
            state = app.class_service.state(class_id)
            unlocked = bool(state.get("unlocked")) or bool(class_data.get("default"))
            y = 200 + index * 145
            app._draw_text(str(class_data.get("name", class_id)), (220, y), app.font, ACCENT_2 if unlocked else TEXT)
            tier = class_data.get("tiers", [{}])[int(state.get("tier", 1)) - 1]
            app._draw_text(f"Palier {tier.get('tier', 1)} : {tier.get('title', '')}", (450, y), app.font_small, TEXT)
            if unlocked:
                app._draw_text("Classe apprise", (700, y), app.font_small, SUCCESS)
                next_tier_index = int(state.get("tier", 1))
                tiers = class_data.get("tiers", [])
                if next_tier_index < len(tiers):
                    threshold = tiers[next_tier_index].get("mastery_required", 0)
                    app._draw_text(f"Maîtrise : {state.get('mastery', 0)} / {threshold}", (350, y + 38), app.font_small, MUTED)
                else:
                    app._draw_text(f"Maîtrise : {state.get('mastery', 0)} (max)", (350, y + 38), app.font_small, MUTED)
            else:
                requirements = app.class_service.requirements(class_id)
                app._draw_text(" | ".join(requirements) or "Disponible", (220, y + 38), app.font_small, MUTED)
        if app.status_feedback:
            app._draw_text(app.status_feedback, (220, 570), app.font_small, TEXT)
        app._draw_buttons(self.buttons(app))
