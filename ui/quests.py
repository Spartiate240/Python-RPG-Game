"""Ecran du tableau de quetes en bois et parchemins."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, PANEL_2, SUCCESS
from ui.widgets import Button


QUESTS_PANEL_RECT = pygame.Rect(70, 55, 1140, 610)
QUESTS_BOARD_RECT = pygame.Rect(105, 125, 1070, 470)
QUESTS_BACK_BUTTON_RECT = pygame.Rect(1035, 610, 150, 48)
NOTE_HEIGHT = 124
NOTE_GAP = 18
NOTE_RECTS = [pygame.Rect(130, 145, 1015, NOTE_HEIGHT)]
SCROLL_STEP = NOTE_HEIGHT + NOTE_GAP


class QuestsScreen:
    """Construit le tableau d'affichage des quetes."""

    def __init__(self) -> None:
        self.scroll_offset = 0

    def _max_scroll(self, app: Any) -> int:
        content_height = len(app.quest_catalog) * SCROLL_STEP - NOTE_GAP
        visible_height = QUESTS_BOARD_RECT.height - 20
        return max(0, content_height - visible_height)

    def scroll(self, app: Any, amount: int) -> None:
        self.scroll_offset = max(0, min(self._max_scroll(app), self.scroll_offset + amount * SCROLL_STEP))

    def handle_key(self, app: Any, key: int) -> None:
        if key == pygame.K_DOWN:
            self.scroll(app, 1)
        elif key == pygame.K_UP:
            self.scroll(app, -1)

    def buttons(self, app: Any) -> list[Button]:
        buttons = [Button("Retour", QUESTS_BACK_BUTTON_RECT, "back")]
        for index, quest in enumerate(app.quest_catalog.values()):
            quest_id = str(quest["id"])
            status = app.progression_manager.quest_status(quest_id)
            if status == "hidden":
                continue
            if status == "available":
                action, label = f"accept_quest:{quest_id}", "Accepter"
            elif status == "claimable":
                action, label = f"claim_quest:{quest_id}", "Réclamer"
            elif quest.get("evaluation_enemy") and status == "active":
                action, label = "pass_evaluation", "Passer l'évaluation"
            else:
                action = "noop"
                label = "Terminé" if status == "claimed" else "En cours"
            rect = self._note_rect(index)
            if not self._is_visible(rect):
                continue
            payload = {"quest_id": quest_id} if action == "pass_evaluation" else {}
            buttons.append(Button(label, pygame.Rect(rect.right - 180, rect.y + 66, 150, 42), action, payload=payload, enabled=action != "noop"))
        return buttons

    def _note_rect(self, index: int) -> pygame.Rect:
        return pygame.Rect(130, 145 + index * SCROLL_STEP - self.scroll_offset, 1015, NOTE_HEIGHT)

    @staticmethod
    def _is_visible(rect: pygame.Rect) -> bool:
        return rect.bottom > QUESTS_BOARD_RECT.top + 8 and rect.top < QUESTS_BOARD_RECT.bottom - 8

    @staticmethod
    def _draw_type_icon(app: Any, center: tuple[int, int], quest_type: str) -> None:
        x, y = center
        if quest_type == "repeatable":
            pygame.draw.arc(app.screen, ACCENT_2, pygame.Rect(x - 12, y - 12, 24, 24), 0.3, 4.8, 3)
            pygame.draw.polygon(app.screen, ACCENT_2, [(x + 10, y - 10), (x + 13, y), (x + 3, y - 3)])
        elif quest_type == "daily":
            pygame.draw.line(app.screen, ACCENT, (x - 6, y - 11), (x + 6, y - 11), 3)
            pygame.draw.line(app.screen, ACCENT, (x - 6, y + 11), (x + 6, y + 11), 3)
            pygame.draw.polygon(app.screen, ACCENT, [(x - 6, y - 9), (x + 6, y - 9), (x + 2, y), (x + 6, y + 9), (x - 6, y + 9), (x - 2, y)])
        else:
            pygame.draw.circle(app.screen, MUTED, (x, y), 9, 2)

    @staticmethod
    def _daily_remaining(app: Any) -> str:
        remaining = app.progression_manager.time_until_daily_reset()
        hours, remainder = divmod(max(0, int(remaining.total_seconds())), 3600)
        return f"Reset dans {hours:02d}h {remainder // 60:02d}m"

    def _draw_note(self, app: Any, quest: dict[str, Any], index: int) -> None:
        rect = self._note_rect(index)
        note = pygame.Surface(rect.size, pygame.SRCALPHA)
        note.fill((190, 151, 91, 255))
        pygame.draw.rect(note, (105, 66, 32), note.get_rect(), width=3, border_radius=4)
        pygame.draw.circle(note, (165, 48, 37), (26, 16), 7)
        pygame.draw.circle(note, (235, 124, 83), (24, 14), 2)
        rotated = pygame.transform.rotate(note, -1.5 if index % 2 == 0 else 1.2)
        app.screen.blit(rotated, rotated.get_rect(center=rect.center))

        quest_id = str(quest["id"])
        quest_type = str(quest.get("type", "unique"))
        status = app.progression_manager.quest_status(quest_id)
        if status == "hidden":
            return
        status_labels = {
            "available": "DISPONIBLE",
            "active": "EN COURS",
            "claimable": "A RECLAMER",
            "claimed": "TERMINE",
        }
        status_colors = {
            "available": ACCENT_2,
            "active": ACCENT,
            "claimable": SUCCESS,
            "claimed": MUTED,
        }
        status_surface = app.font_small.render(status_labels.get(status, status.upper()), True, status_colors.get(status, MUTED))
        app.screen.blit(status_surface, status_surface.get_rect(topright=(rect.right - 205, rect.y + 14)))
        self._draw_type_icon(app, (rect.x + 52, rect.y + 34), quest_type)
        app._draw_text(str(quest.get("name", quest_id)), (rect.x + 82, rect.y + 14), app.font, (58, 37, 20))
        app._draw_text(str(quest.get("description", "")), (rect.x + 82, rect.y + 47), app.font_small, (72, 47, 26))

        conditions = quest.get("conditions", {})
        conditions = conditions if isinstance(conditions, list) else [conditions]
        progress = [app.progression_manager.condition_progress(condition, quest_id) for condition in conditions]
        progress_label = "  ".join(f"{current}/{target}" for current, target in progress)
        app._draw_text(f"Progression : {progress_label}", (rect.x + 82, rect.y + 78), app.font_small, (72, 47, 26))
        if status in ("active", "claimable"):
            bar_x, bar_y, bar_w = rect.x + 82, rect.y + 103, 300
            pygame.draw.rect(app.screen, (99, 63, 34), pygame.Rect(bar_x, bar_y, bar_w, 8), border_radius=4)
            ratio = min(1.0, min((current / target) if target else 1.0 for current, target in progress))
            pygame.draw.rect(app.screen, SUCCESS, pygame.Rect(bar_x, bar_y, int(bar_w * ratio), 8), border_radius=4)
        if quest_type == "daily":
            app._draw_text(self._daily_remaining(app), (rect.x + 500, rect.y + 82), app.font_small, (72, 47, 26))
        if quest_type == "repeatable":
            count = app.progression.get("quests", {}).get("completions", {}).get(quest_id, 0)
            app._draw_text(f"Accomplie {count} fois", (rect.x + 500, rect.y + 57), app.font_small, (72, 47, 26))

    def render(self, app: Any) -> None:
        app._draw_panel(QUESTS_PANEL_RECT, PANEL)
        board = app.renderer.panel_surface(QUESTS_BOARD_RECT.size, "freefantasy", "ff_001", PANEL_2)
        app.screen.blit(board, QUESTS_BOARD_RECT.topleft)
        app._draw_text("Tableau des quêtes", (115, 82), app.font_big, ACCENT)
        app._draw_text("Les missions du village sont épinglées ici.", (690, 91), app.font_small, MUTED)

        previous_clip = app.screen.get_clip()
        app.screen.set_clip(QUESTS_BOARD_RECT.inflate(-24, -16))
        for index, quest in enumerate(app.quest_catalog.values()):
            if app.progression_manager.quest_status(str(quest["id"])) != "hidden" and self._is_visible(self._note_rect(index)):
                self._draw_note(app, quest, index)
        app.screen.set_clip(previous_clip)
        self._draw_scrollbar(app)
        app._draw_buttons(self.buttons(app))

    def _draw_scrollbar(self, app: Any) -> None:
        if self._max_scroll(app) == 0:
            return
        track = pygame.Rect(1155, QUESTS_BOARD_RECT.top + 12, 8, QUESTS_BOARD_RECT.height - 24)
        pygame.draw.rect(app.screen, (82, 51, 28), track, border_radius=4)
        thumb_height = max(32, int(track.height * (track.height / (track.height + self._max_scroll(app)))))
        travel = track.height - thumb_height
        thumb_y = track.y + int(travel * self.scroll_offset / self._max_scroll(app))
        pygame.draw.rect(app.screen, ACCENT, pygame.Rect(track.x, thumb_y, track.width, thumb_height), border_radius=4)
