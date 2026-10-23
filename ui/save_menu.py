"""Ecran de creation et de selection des sauvegardes."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, DANGER, MUTED, PANEL, PANEL_2, TEXT
from ui.widgets import Button


class SaveMenuScreen:
    """Permet de choisir une sauvegarde ou de nommer une nouvelle partie."""

    def __init__(self) -> None:
        self.mode = "load"
        self.name = ""
        self.error = ""
        self._submit_name = False

    def open(self, mode: str) -> None:
        self.mode = mode
        self.name = ""
        self.error = ""

    def handle_key(self, event: pygame.event.Event) -> None:
        if self.mode != "create":
            return
        if event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif event.key == pygame.K_RETURN:
            self._submit_name = True
        elif event.unicode and event.unicode.isprintable() and len(self.name) < 24:
            self.name += event.unicode

    def buttons(self, app: Any) -> list[Button]:
        if self.mode == "create":
            return [
                Button("Commencer", pygame.Rect(700, 500, 230, 55), "create_named_game", enabled=bool(self.name.strip())),
                Button("Retour", pygame.Rect(960, 500, 180, 55), "save_back"),
            ]
        buttons = []
        for index, slot in enumerate(app.save_manager.list_slots()):
            buttons.append(Button(slot.label, pygame.Rect(160, 190 + index * 72, 760, 56), "load_slot", payload={"path": str(slot.path), "ui_icon": 16}))
        buttons.append(Button("Nouvelle partie", pygame.Rect(160, 560, 300, 50), "new_named_game"))
        buttons.append(Button("Retour", pygame.Rect(980, 560, 170, 50), "save_back"))
        return buttons

    def submit_requested(self) -> bool:
        requested = getattr(self, "_submit_name", False)
        self._submit_name = False
        return requested

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(70, 70, 1140, 590), PANEL)
        if self.mode == "create":
            app._draw_text("Nouvelle partie", (120, 120), app.font_big, ACCENT)
            app._draw_text("Nom du personnage", (160, 245), app.font, TEXT)
            app._draw_panel(pygame.Rect(160, 290, 720, 58), PANEL_2)
            app._draw_text(self.name or "Entre un nom...", (180, 305), app.font, TEXT if self.name else MUTED)
            app._draw_text("Le nom sera conserve dans une nouvelle sauvegarde.", (160, 390), app.font_small, MUTED)
            if self.error:
                app._draw_text(self.error, (160, 445), app.font_small, DANGER)
        else:
            app._draw_text("Choisir une sauvegarde", (120, 120), app.font_big, ACCENT)
            slots = app.save_manager.list_slots()
            if not slots:
                app._draw_text("Aucune sauvegarde trouvee.", (160, 210), app.font, MUTED)
            else:
                app._draw_text("Selectionne une partie a reprendre.", (160, 155), app.font_small, MUTED)
                for index, slot in enumerate(slots):
                    y = 190 + index * 72
                    app._draw_text("Sauvegarde locale" if not slot.legacy else "Sauvegarde principale", (210, y + 31), app.font_small, MUTED)
                    app._draw_text(slot.path.stem, (680, y + 31), app.font_small, ACCENT)
        app._draw_buttons(self.buttons(app))

    def click(self, app: Any, position: tuple[int, int]) -> None:
        app._handle_buttons(position, self.buttons(app))
