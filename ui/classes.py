"""Ecran d'apprentissage des classes."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, SUCCESS, TEXT
from ui.widgets import Button


class ClassesScreen:
    """Affiche les cartes de choix de classe et leur emblème."""

    def buttons(self, app: Any) -> list[Button]:
        buttons = [Button("Retour", pygame.Rect(1075, 610, 130, 40), "back")]
        card_width = 270
        gap = 15
        for index, class_id in enumerate(app.catalogs.classes):
            class_data = app.catalogs.classes[class_id]
            buttons.append(
                Button(
                    "Choisir",
                    pygame.Rect(80 + index * (card_width + gap), 555, card_width, 48),
                    f"choose_class:{class_id}",
                )
            )
        return buttons

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(60, 50, 1160, 610), PANEL)
        app._draw_text("Choisir une classe", (95, 85), app.font_big, ACCENT)
        app._draw_text("Chaque voie possède ses propres statistiques et tiers.", (95, 135), app.font_small, MUTED)
        if app.party is not None and app.party.leader is not None:
            app._draw_text(
                f"Classe actuelle : {app.party.leader.class_name} — le changement conserve le niveau et l'XP, mais recommence au tier 1.",
                (95, 155),
                app.font_small,
                TEXT,
            )
        for index, class_id in enumerate(app.catalogs.classes):
            class_data = app.catalogs.classes[class_id]
            rect = pygame.Rect(65 + index * 285, 175, 270, 350)
            is_necromancer = class_id == "necromancer"
            card_color = (35, 27, 38) if is_necromancer else (74, 49, 29)
            app._draw_panel(rect, card_color)
            icon_id = {"sword": 23, "staff": 24, "bow": 25, "skull": 26}.get(class_data.get("emblem"), 23)
            icon = app.renderer.load_asset_sprite("icons", str(icon_id), (64, 64))
            if is_necromancer:
                icon = icon.copy()
                icon.fill((82, 70, 105, 190), special_flags=pygame.BLEND_RGBA_MULT)
            app.screen.blit(icon, icon.get_rect(center=(rect.centerx, rect.y + 72)))
            app._draw_centered_text(str(class_data.get("name", class_id)), (rect.centerx, rect.y + 145), app.font, (151, 126, 181) if is_necromancer else ACCENT_2)
            description = str(class_data.get("description", ""))
            words, line = description.split(), ""
            lines: list[str] = []
            for word in words:
                candidate = f"{line} {word}".strip()
                if line and app.font_small.size(candidate)[0] > rect.width - 28:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            if line:
                lines.append(line)
            for line_index, text in enumerate(lines[:3]):
                app._draw_centered_text(text, (rect.centerx, rect.y + 180 + line_index * 20), app.font_small, TEXT)
            stats = class_data.get("base_stats", {})
            stat_labels = (("PV", "max_hp"), ("ATQ", "attack"), ("DEF", "defense"), ("VIT", "speed"))
            for stat_index, (label, key) in enumerate(stat_labels):
                x = rect.x + 24 + (stat_index % 2) * 118
                y = rect.y + 250 + (stat_index // 2) * 30
                app._draw_text(f"{label} {stats.get(key, 0)}", (x, y), app.font_small, MUTED)
            app._draw_centered_text("Tier 1", (rect.centerx, rect.y + 315), app.font_small, TEXT)
        if app.status_feedback:
            app._draw_text(app.status_feedback, (220, 570), app.font_small, TEXT)
        app._draw_buttons(self.buttons(app))

    @staticmethod
    def draw_emblem(app: Any, emblem: str, x: int, y: int) -> None:
        color = ACCENT
        if emblem == "staff":
            pygame.draw.line(app.screen, color, (x - 10, y + 35), (x + 8, y - 35), 8)
            pygame.draw.circle(app.screen, color, (x + 12, y - 38), 12, 3)
        elif emblem == "bow":
            pygame.draw.arc(app.screen, color, pygame.Rect(x - 28, y - 38, 56, 76), -1.2, 1.2, 6)
            pygame.draw.line(app.screen, color, (x - 10, y - 30), (x - 10, y + 30), 3)
            pygame.draw.line(app.screen, color, (x - 10, y), (x + 30, y), 4)
        else:
            pygame.draw.line(app.screen, color, (x - 25, y + 25), (x + 25, y - 25), 8)
            pygame.draw.line(app.screen, color, (x - 10, y + 8), (x + 8, y + 26), 7)
            pygame.draw.line(app.screen, color, (x - 25, y + 25), (x - 38, y + 38), 5)
