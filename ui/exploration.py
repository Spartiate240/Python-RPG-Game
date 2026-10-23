"""Ecran d'exploration."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, PANEL_2, SUCCESS, TEXT
from ui.widgets import Button
from ui.ceremony import draw_rank_badge


class ExplorationScreen:
    """Construit le rendu de l'exploration depuis l'etat de l'application."""

    @staticmethod
    def rank_badge_rect(member_rect: pygame.Rect) -> pygame.Rect:
        return pygame.Rect(member_rect.right - 68, member_rect.y - 1, 52, 52)

    @staticmethod
    def buttons() -> list[Button]:
        return [
            Button("Régions", pygame.Rect(800, 225, 320, 48), "regions", payload={"ui_icon": 16}),
            Button("Rencontre", pygame.Rect(800, 275, 320, 48), "encounter", payload={"ui_icon": 17}),
            Button("Boutique", pygame.Rect(800, 325, 320, 48), "shop", payload={"ui_icon": 18}),
            Button("Tableau des quêtes", pygame.Rect(800, 375, 320, 48), "quests", payload={"ui_icon": 19}),
            Button("Titres", pygame.Rect(800, 425, 320, 48), "titles", payload={"ui_icon": 20}),
            Button("Inventaire", pygame.Rect(800, 475, 320, 48), "status", payload={"ui_icon": 21}),
            Button("Changer de classe", pygame.Rect(800, 525, 320, 48), "classes", payload={"ui_icon": 22}),
            Button("Sauvegarder", pygame.Rect(800, 575, 155, 48), "save", sprite_theme="freefantasy", sprite_id="ff_002"),
            Button("Quitter", pygame.Rect(965, 575, 155, 48), "quit", sprite_theme="freefantasy", sprite_id="ff_002"),
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
            holder = app.renderer.load_asset_sprite("holders", "2", (64, 64))
            app.screen.blit(holder, holder.get_rect(center=(rect.x + 41, rect.y + 42)))
            sprite = app._load_sprite("data/assets/sprites/player/ff_000.png", (54, 54), "Joueur")
            app.screen.blit(sprite, (rect.x + 14, rect.y + 15))
            app._draw_text(member.name, (rect.x + 82, rect.y + 10), app.font, TEXT)
            if member is app.party.leader:
                badge_rect = ExplorationScreen.rank_badge_rect(rect)
                draw_rank_badge(app, badge_rect.center, member.rank, 26)
            app._draw_text(
                f"HP {member.hp}/{member.max_hp}  ATQ {getattr(member, 'total_attack', member.attack)}  DEF {getattr(member, 'total_defense', member.defense)}",
                (rect.x + 82, rect.y + 42),
                app.font_small,
                MUTED,
            )

        leader = app.party.leader
        if leader is not None and app.party.members:
            leader_rect = pygame.Rect(x, y, 430, 84)
            badge_rect = ExplorationScreen.rank_badge_rect(leader_rect)
            if badge_rect.collidepoint(pygame.mouse.get_pos()):
                rank = app.catalogs.ranks.get(getattr(leader, "rank", "iron"), {})
                tooltip = pygame.Rect(badge_rect.x - 155, badge_rect.bottom + 8, 205, 64)
                surface = pygame.Surface(tooltip.size, pygame.SRCALPHA)
                surface.fill((190, 151, 91, 250))
                pygame.draw.rect(surface, (105, 66, 32), surface.get_rect(), width=3, border_radius=5)
                label = app.font_small.render(f"Rang : {rank.get('name', 'Fer')}", True, (58, 37, 20))
                surface.blit(label, label.get_rect(center=(tooltip.width // 2, tooltip.height // 2)))
                app.screen.blit(surface, tooltip.topleft)

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

