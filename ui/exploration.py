"""Ecran d'exploration."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, PANEL_2, SUCCESS, TEXT
from ui.widgets import Button


class ExplorationScreen:
    """Construit le rendu de l'exploration depuis l'etat de l'application."""

    @staticmethod
    def buttons() -> list[Button]:
        return [
            Button("Régions", pygame.Rect(800, 225, 320, 48), "regions", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Rencontre", pygame.Rect(800, 275, 320, 48), "encounter", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Boutique", pygame.Rect(800, 325, 320, 48), "shop", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Tableau des quêtes", pygame.Rect(800, 375, 320, 48), "quests", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Titres", pygame.Rect(800, 425, 320, 48), "titles", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Inventaire", pygame.Rect(800, 475, 320, 48), "status", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder", pygame.Rect(800, 525, 320, 48), "save", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder et quitter", pygame.Rect(800, 575, 320, 48), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
        ]

    @staticmethod
    def draw_party_summary(app: Any, position: tuple[int, int]) -> None:
        if app.party is None:
            app._draw_text("Aucun groupe.", position, app.font, MUTED)
            return
        x, y = position
        for index, member in enumerate(app.party.members):
            rect = pygame.Rect(x, y + index * 96, 430, 84)
            app._draw_panel(rect, (22, 30, 48))
            sprite = app._load_sprite("data/assets/sprites/player/ff_000.png", (54, 54), "Joueur")
            app.screen.blit(sprite, (rect.x + 14, rect.y + 15))
            app._draw_text(member.name, (rect.x + 82, rect.y + 10), app.font, TEXT)
            app._draw_text(
                f"HP {member.hp}/{member.max_hp}  ATQ {getattr(member, 'total_attack', member.attack)}  DEF {getattr(member, 'total_defense', member.defense)}",
                (rect.x + 82, rect.y + 42),
                app.font_small,
                MUTED,
            )

    def render(self, app: Any) -> None:
        app._draw_panel(pygame.Rect(50, 60, 580, 620), PANEL)
        app._draw_panel(pygame.Rect(660, 60, 570, 620), PANEL_2)
        app._draw_text("Etat du Groupe", (95, 100), app.font_big, ACCENT)

        zone = app.catalogs.zone_for_id(app.location or "village") or {}
        region_id = app.catalogs.region_for_zone(app.location)
        region = app.region_catalog.get(region_id or "", {})
        app._draw_text(
            f"Région: {region.get('name', 'Inconnue')}",
            (80, 150),
            app.font,
            SUCCESS,
        )
        app._draw_text(
            f"Zone: {zone.get('name', app.location or 'Village')}",
            (430, 150),
            app.font,
            SUCCESS,
        )
        gold = app.party.leader.gold if app.party and app.party.leader else 0
        app._draw_text(f"Or: {gold}", (275, 193), app.font, SUCCESS)
        app._draw_buttons(self.buttons())
        self.draw_party_summary(app, (125, 225))

        app._draw_centered_text("Exploration", (955, 150), app.font_big, ACCENT_2)

