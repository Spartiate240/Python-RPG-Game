"""Ecran de combat."""

from __future__ import annotations

from typing import Any

import pygame

from entities.combatant import Combatant
from entities.enemy import Enemy
from entities.player import Player
from ui.theme import ACCENT, DANGER, MUTED, PANEL, PANEL_2, SUCCESS, TEXT
from ui.widgets import Button


class BattleScreen:
    """Construit le rendu du combat depuis l'etat de l'application."""

    @staticmethod
    def label(app: Any) -> str:
        if app.battle is None:
            return ""
        if app.battle.result == "victory":
            return "Victoire"
        if app.battle.result == "defeat":
            return "Défaite"
        if app.battle.result == "flee":
            return "Fuite"
        return f"Tour de {getattr(app.battle.current_actor, 'name', '...')}"

    @staticmethod
    def enemy_rects(app: Any) -> list[tuple[Enemy, pygame.Rect]]:
        if app.battle is None:
            return []
        enemies = [enemy for enemy in app.battle.enemies if enemy.is_alive()]
        return [(enemy, pygame.Rect(90 + index * 220, 455, 160, 160)) for index, enemy in enumerate(enemies)]

    @staticmethod
    def draw_actor_card(app: Any, combatant: Combatant, rect: pygame.Rect, sprite: pygame.Surface, tint: tuple[int, int, int], sprite_center_y: int | None = None) -> None:
        app._draw_panel(rect, (23, 33, 52))
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((*tint, 35))
        app.screen.blit(overlay, rect.topleft)
        if sprite_center_y is None:
            sprite_center_y = rect.y + sprite.get_height() // 2 + 8
        app.screen.blit(sprite, sprite.get_rect(center=(rect.centerx, sprite_center_y)))
        app._draw_centered_text(combatant.name, (rect.centerx, rect.bottom - 34), app.font_small, TEXT)
        app._draw_centered_text(
            f"HP {combatant.hp}/{combatant.max_hp}",
            (rect.centerx, rect.bottom - 14),
            app.font_small,
            SUCCESS if combatant.is_alive() else DANGER,
        )

    def draw_cards(self, app: Any) -> None:
        if app.party is None or app.battle is None:
            return
        allies = [member for member in app.party.active_members() if member.is_alive()]
        hero_sprite = pygame.transform.smoothscale(app._main_hero_sprite(), (80, 80))
        for index, member in enumerate(allies):
            self.draw_actor_card(app, member, pygame.Rect(90 + index * 180, 275, 160, 160), hero_sprite, (230, 245, 255), sprite_center_y=360)
        enemy_sprite = app._load_sprite(app._enemy_sprite_path(), (80, 80), "Ennemi")
        for enemy, rect in self.enemy_rects(app):
            self.draw_actor_card(app, enemy, rect, enemy_sprite, (255, 220, 220), sprite_center_y=rect.y + 75)
            if isinstance(app.battle.current_actor, Player) and rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(app.screen, ACCENT, rect, width=4, border_radius=18)

    def action_buttons(self, app: Any) -> list[Button]:
        buttons = [
            Button(
                "Attaque normale",
                pygame.Rect(700, 510, 220, 48),
                "select_attack",
                enabled=app.selected_battle_action != "attack",
            )
        ]
        if app.battle is not None and isinstance(app.battle.current_actor, Player):
            for index, item in enumerate(app.catalogs.items.values()):
                quantity = int(app.inventory.get("items", {}).get(item["id"], 0))
                if quantity <= 0 or item.get("effect") != "heal":
                    continue
                buttons.append(
                    Button(
                        f"{item.get('name', item['id'])} x{quantity}",
                        pygame.Rect(950, 510 + index * 36, 220, 32),
                        "use_item",
                        payload={"item_id": item["id"]},
                    )
                )
            for index, skill in enumerate(app.battle.available_skills(app.battle.current_actor)):
                buttons.append(
                    Button(
                        skill.name,
                        pygame.Rect(700, 565 + index * 48, 220, 42),
                        "select_skill",
                        payload={"skill_id": skill.id},
                        enabled=app.selected_battle_skill_id != skill.id,
                    )
                )
        buttons.append(Button("Fuir", pygame.Rect(950, 580, 190, 50), "flee", sprite_theme="freefantasy", sprite_id="ff_002"))
        return buttons

    @staticmethod
    def result_buttons() -> list[Button]:
        return [
            Button("Continuer", pygame.Rect(890, 550, 240, 56), "continue", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Retour", pygame.Rect(890, 605, 240, 40), "battle_menu", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    def render(self, app: Any) -> None:
        if app.battle is None:
            app.state = "exploration"
            return

        app._draw_panel(pygame.Rect(50, 60, 1180, 620), PANEL)
        app._draw_text("Combat", (95, 100), app.font_big, ACCENT)
        app._draw_text(self.label(app), (95, 150), app.font, MUTED)
        self.draw_cards(app)

        if app.battle.result is not None:
            app._draw_panel(pygame.Rect(840, 510, 340, 140), PANEL_2)
            app._draw_centered_text(
                self.label(app),
                (1010, 470),
                app.font_big,
                SUCCESS if app.battle.result == "victory" else DANGER,
            )
            app._draw_buttons(self.result_buttons())
            return

        if isinstance(app.battle.current_actor, Player):
            action_label = (
                "une attaque normale"
                if app.selected_battle_action == "attack"
                else "le skill sélectionné"
            )
            app._draw_centered_text(
                f"Sélectionne {action_label}, puis une cible",
                (940, 480),
                app.font_small,
                MUTED,
            )
        app._draw_buttons(self.action_buttons(app))

    def handle_click(self, app: Any, position: tuple[int, int]) -> None:
        """Traite les clics propres au combat sans calculer les regles de combat."""
        if app.battle is None:
            return
        if app.battle.result is not None:
            app._handle_buttons(position, self.result_buttons())
            return

        actor = app.battle.current_actor
        if actor is None or not isinstance(actor, Player):
            return

        for enemy, rect in self.enemy_rects(app):
            if rect.collidepoint(position):
                if app.selected_battle_action == "attack":
                    app.battle.player_attack(enemy)
                elif app.selected_battle_skill_id is not None:
                    app.battle.player_skill(app.selected_battle_skill_id, enemy)
                app.selected_battle_action = "attack"
                app.selected_battle_skill_id = None
                return

        app._handle_buttons(position, self.action_buttons(app))
