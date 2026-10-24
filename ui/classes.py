"""Ecran navigable des voies, tiers et specialisations."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, DANGER, MUTED, PANEL, PANEL_2, SUCCESS, TEXT
from ui.widgets import Button


class ClassesScreen:
    """Affiche une voie a la fois et conserve l'arbre visible dans la meme vue."""

    def _selected_id(self, app: Any) -> str:
        selected = getattr(app, "selected_class_id", None)
        if selected in app.catalogs.classes:
            return selected
        return next(iter(app.catalogs.classes), "warrior")

    def buttons(self, app: Any) -> list[Button]:
        buttons = [Button("Retour", pygame.Rect(1075, 625, 130, 40), "back")]
        class_ids = list(app.catalogs.classes)
        for index, class_id in enumerate(class_ids):
            row = index % 10
            buttons.append(Button(app.catalogs.classes[class_id].get("name", class_id), pygame.Rect(75, 125 + row * 43, 205, 35), f"class_view:{class_id}"))
        class_data = app.catalogs.classes.get(self._selected_id(app), {})
        for tier in class_data.get("tiers", []):
            tier_id = int(tier.get("tier", 1))
            for node_index, node in enumerate(tier.get("nodes", [])):
                x = 330 + (tier_id - 1) * 175
                y = 190 + node_index * 92
                buttons.append(Button("Choisir", pygame.Rect(x, y + 47, 150, 28), f"choose_node:{node.get('id')}"))
        return buttons

    def render(self, app: Any) -> None:
        selected_id = self._selected_id(app)
        app.selected_class_id = selected_id
        class_data = app.catalogs.classes.get(selected_id, {})
        state = app.class_service.state(selected_id)
        app._draw_panel(pygame.Rect(45, 35, 1190, 640), PANEL)
        app._draw_text("Voies et spécialisations", (75, 62), app.font_big, ACCENT)
        app._draw_text("Choisissez une voie, puis suivez sa progression de tier en tier.", (75, 105), app.font_small, MUTED)
        app._draw_panel(pygame.Rect(65, 125, 225, 470), PANEL_2)
        for index, class_id in enumerate(app.catalogs.classes):
            color = ACCENT if class_id == selected_id else TEXT
            app._draw_text(str(app.catalogs.classes[class_id].get("name", class_id)), (82, 133 + index * 43), app.font_small, color)
        app._draw_panel(pygame.Rect(310, 125, 890, 470), (63, 42, 25))
        app._draw_text(str(class_data.get("name", selected_id)), (335, 143), app.font, ACCENT_2)
        app._draw_text(f"Maîtrise : {state['mastery']} / {state['mastery_required']}", (700, 148), app.font_small, SUCCESS if state["mastery"] >= state["mastery_required"] else MUTED)
        app._draw_text(str(class_data.get("description", "")), (335, 176), app.font_small, TEXT)
        leader = app.party.leader if app.party else None
        level = int(getattr(leader, "level", 1))
        for tier in class_data.get("tiers", []):
            tier_id = int(tier.get("tier", 1))
            x = 330 + (tier_id - 1) * 175
            unlocked = bool(leader and leader.class_id == selected_id and tier_id <= int(leader.tier))
            requirement = int(tier.get("requirements", {}).get("min_level", tier_id * 20)) if tier_id > 1 else 1
            app._draw_text(f"T{tier_id}  Nv.{requirement}", (x, 220), app.font_small, SUCCESS if unlocked else MUTED)
            for node_index, node in enumerate(tier.get("nodes", [])):
                y = 255 + node_index * 92
                node_id = str(node.get("id"))
                selected = node_id == getattr(leader, "class_node_id", None)
                color = ACCENT if selected else TEXT
                app._draw_panel(pygame.Rect(x, y, 160, 75), (91, 62, 34) if selected else PANEL_2)
                app._draw_centered_text(str(node.get("name", node_id)), (x + 80, y + 18), app.font_small, color)
                skills = ", ".join(str(skill) for skill in node.get("skills", [])) or "Aucun skill"
                app._draw_centered_text(skills[:22], (x + 80, y + 40), app.font_small, MUTED)
                percent = node.get("percent_bonus", {})
                if percent:
                    bonus = ", ".join(f"{key} +{value}%" for key, value in percent.items())
                    app._draw_centered_text(bonus[:23], (x + 80, y + 60), app.font_small, SUCCESS)
        if app.status_feedback:
            app._draw_text(app.status_feedback, (325, 610), app.font_small, DANGER if "pas" in app.status_feedback.lower() else TEXT)
        app._draw_buttons(self.buttons(app))
