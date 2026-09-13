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
            Button("Régions", pygame.Rect(800, 200, 320, 48), "regions", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Rencontre", pygame.Rect(800, 255, 320, 48), "encounter", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Boutique", pygame.Rect(800, 309, 320, 48), "shop", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Tableau des quêtes", pygame.Rect(800, 363, 320, 48), "quests", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Titres", pygame.Rect(800, 417, 320, 48), "titles", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("État du groupe", pygame.Rect(800, 471, 320, 48), "status", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder", pygame.Rect(800, 525, 320, 48), "save", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Sauvegarder et quitter", pygame.Rect(800, 579, 320, 48), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
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
        app._draw_text("Exploration", (95, 100), app.font_big, ACCENT)
        app._draw_text(
            "Le groupe avance dans les terres hostiles.",
            (95, 150),
            app.font,
            MUTED,
        )
        zone = app.catalogs.zone_for_id(app.location or "village") or {}
        region_id = app.catalogs.region_for_zone(app.location)
        region = app.region_catalog.get(region_id or "", {})
        app._draw_text(
            f"Région: {region.get('name', 'Inconnue')}",
            (95, 190),
            app.font,
            ACCENT_2,
        )
        app._draw_text(
            f"Zone: {zone.get('name', app.location or 'Village')}",
            (95, 225),
            app.font,
            ACCENT_2,
        )
        gold = app.party.leader.gold if app.party and app.party.leader else 0
        app._draw_text(f"Or: {gold}", (95, 260), app.font, SUCCESS)
        app._draw_buttons(self.buttons())
        self.draw_party_summary(app, (125, 270))

        app._draw_centered_text("Prêt à explorer", (945, 205), app.font_big, ACCENT_2)
        app._draw_centered_text(
            "Clique sur Rencontre pour lancer un combat.",
            (945, 250),
            app.font_small,
            MUTED,
        )
