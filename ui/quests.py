"""Ecran du tableau des quetes."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, MUTED, PANEL, PANEL_2, TEXT
from ui.widgets import Button


QUESTS_PANEL_RECT = pygame.Rect(70, 55, 1140, 610)
QUESTS_BOARD_RECT = pygame.Rect(105, 125, 1070, 470)
QUESTS_BACK_BUTTON_RECT = pygame.Rect(1035, 610, 150, 48)


class QuestsScreen:
    """Construit le rendu du tableau des quetes."""

    def buttons(self, app: Any) -> list[Button]:
        buttons = [Button("Retour", QUESTS_BACK_BUTTON_RECT, "back")]
        for index, quest in enumerate(app.quest_catalog.values()):
            quest_id = str(quest["id"])
            status = app.progression_manager.quest_status(quest_id)
            if status == "available":
                action, label = f"accept_quest:{quest_id}", "Accepter"
            elif status == "claimable":
                action, label = f"claim_quest:{quest_id}", "Réclamer"
            else:
                action = "noop"
                label = "Terminé" if status == "claimed" else "En cours"
            buttons.append(Button(label, pygame.Rect(1000, 165 + index * 112, 145, 42), action, enabled=action != "noop"))
        return buttons

    def render(self, app: Any) -> None:
        app._draw_panel(QUESTS_PANEL_RECT, PANEL)
        board = app.renderer.panel_surface(QUESTS_BOARD_RECT.size, "freefantasy", "ff_001", PANEL_2)
        app.screen.blit(board, QUESTS_BOARD_RECT.topleft)
        app._draw_text("Tableau des quêtes", (115, 82), app.font_big, ACCENT)
        app._draw_text(
            "Les tâches proposées par les habitants du village",
            (115, 110),
            app.font_small,
            MUTED,
        )
        for index, quest in enumerate(app.quest_catalog.values()):
            y = 150 + index * 112
            app._draw_text(str(quest.get("name", quest["id"])), (145, y), app.font, ACCENT)
            app._draw_text(str(quest.get("description", "")), (145, y + 30), app.font_small, TEXT)
            conditions = quest.get("conditions", {})
            conditions = conditions if isinstance(conditions, list) else [conditions]
            progress = ", ".join(
                f"{current}/{target}"
                for current, target in (
                    app.progression_manager.condition_progress(condition) for condition in conditions
                )
            )
            app._draw_text(f"Avancement: {progress}", (145, y + 56), app.font_small, MUTED)
        app._draw_buttons(self.buttons(app))
