"""Rendu pygame partage entre les ecrans."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, BG, BG_2, MUTED, TEXT
from ui.widgets import Button


ROOT_DIR = Path(__file__).resolve().parents[1]
UI_DIR = ROOT_DIR / "data" / "assets" / "sprites" / "UI"
SCREEN_SIZE = (1280, 720)


class UIRenderer:
    """Centralise le rendu des panneaux, boutons, textes et sprites."""

    def __init__(self, app: Any) -> None:
        self.app = app

    def draw_background(self) -> None:
        self.app.screen.fill(BG)
        pygame.draw.rect(
            self.app.screen,
            BG_2,
            pygame.Rect(0, SCREEN_SIZE[1] // 2, SCREEN_SIZE[0], SCREEN_SIZE[1] // 2),
        )

    def draw_panel(self, rect: pygame.Rect, color: tuple[int, int, int]) -> None:
        panel = self.panel_surface(rect.size, "freefantasy", "ff_006", color)
        self.app.screen.blit(panel, rect.topleft)
        pygame.draw.rect(self.app.screen, ACCENT_2, rect, width=2, border_radius=18)

    def draw_text(
        self,
        text: str,
        position: tuple[int, int],
        font: pygame.font.Font | None = None,
        color: tuple[int, int, int] = TEXT,
    ) -> None:
        self.app.screen.blit((font or self.app.font).render(text, True, color), position)

    def draw_centered_text(
        self,
        text: str,
        center: tuple[int, int],
        font: pygame.font.Font | None = None,
        color: tuple[int, int, int] = TEXT,
    ) -> None:
        surface = (font or self.app.font).render(text, True, color)
        self.app.screen.blit(surface, surface.get_rect(center=center))

    def draw_buttons(self, buttons: list[Button]) -> None:
        for button in buttons:
            self.app.screen.blit(self.button_surface(button), button.rect.topleft)

    def load_sprite(
        self,
        relative_path: str | None,
        size: tuple[int, int],
        fallback_label: str,
    ) -> pygame.Surface:
        key = (relative_path or fallback_label, size)
        if key in self.app.sprite_cache:
            return self.app.sprite_cache[key]

        surface = pygame.Surface(size, pygame.SRCALPHA)
        if relative_path:
            path = Path(relative_path)
            if not path.is_absolute():
                path = ROOT_DIR / relative_path
            if path.exists():
                image = pygame.image.load(str(path)).convert_alpha()
                image = pygame.transform.smoothscale(image, size)
                pygame.draw.rect(image, ACCENT_2, image.get_rect(), width=2, border_radius=12)
                self.app.sprite_cache[key] = image
                return image

        surface.fill((51, 65, 85))
        pygame.draw.rect(surface, ACCENT_2, surface.get_rect(), width=2, border_radius=12)
        label = self.app.font_small.render(fallback_label, True, TEXT)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        self.app.sprite_cache[key] = surface
        return surface

    def item_sprite_path(self, item: object | None) -> str | None:
        if item is None:
            return None
        sprite = item.get("sprite") if isinstance(item, dict) else getattr(item, "sprite", None)
        if sprite:
            path = Path(sprite)
            if not path.is_absolute():
                path = ROOT_DIR / "data" / sprite
            if path.exists():
                return str(path)

        item_id = self.app.inventory_manager.item_id(item)
        slot = self.app.inventory_manager.item_slot(item)
        weapon_fallbacks = {
            "iron_sword": ROOT_DIR / "data" / "assets" / "sprites" / "weapons" / "iron_sword.png",
            "fire_staff": ROOT_DIR / "data" / "assets" / "sprites" / "weapons" / "fire_staff.png",
        }
        armor_fallbacks = {
            "leather_armor": ROOT_DIR / "data" / "assets" / "sprites" / "armor" / "fa1857.png",
            "chainmail_armor": ROOT_DIR / "data" / "assets" / "sprites" / "armor" / "fa1860.png",
            "plate_armor": ROOT_DIR / "data" / "assets" / "sprites" / "armor" / "fa1893.png",
        }
        fallbacks = weapon_fallbacks if slot == "weapon" else armor_fallbacks if slot else {}
        fallback = fallbacks.get(item_id)
        if fallback is not None and fallback.exists():
            return str(fallback)
        return next((str(candidate) for candidate in fallbacks.values() if candidate.exists()), None)

    def load_item_sprite(self, item: object | None, size: tuple[int, int]) -> pygame.Surface:
        path = self.item_sprite_path(item)
        if path is None:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surface, ACCENT_2, surface.get_rect(), width=2, border_radius=6)
            return surface
        image = pygame.transform.smoothscale(pygame.image.load(path).convert_alpha(), size)
        pygame.draw.rect(image, ACCENT_2, image.get_rect(), width=1, border_radius=6)
        return image

    def load_manifest(self, theme: str) -> list[dict[str, Any]]:
        if theme in self.app.ui_manifest_cache:
            return self.app.ui_manifest_cache[theme]
        manifest_path = UI_DIR / theme / "manifest.json"
        if not manifest_path.exists():
            self.app.ui_manifest_cache[theme] = []
            return []
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.app.ui_manifest_cache[theme] = manifest
        return manifest

    def load_ui_sprite(
        self,
        theme: str,
        sprite_id: str,
        size: tuple[int, int] | None = None,
    ) -> pygame.Surface:
        cache_key = (theme, sprite_id, size)
        if cache_key in self.app.ui_sprite_cache:
            return self.app.ui_sprite_cache[cache_key]
        extracted_path = UI_DIR / theme / f"{sprite_id}.png"
        sprite = (
            pygame.image.load(str(extracted_path)).convert_alpha()
            if extracted_path.exists()
            else self.crop_ui_sprite(theme, sprite_id)
        )
        if size is not None and sprite.get_size() != size:
            sprite = pygame.transform.smoothscale(sprite, size)
        self.app.ui_sprite_cache[cache_key] = sprite
        return sprite

    def crop_ui_sprite(self, theme: str, sprite_id: str) -> pygame.Surface:
        manifest = self.load_manifest(theme)
        entry = next((item for item in manifest if item.get("id") == sprite_id), None)
        sheet_path = UI_DIR / f"{theme}_index.png"
        if entry is None or not sheet_path.exists():
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        if theme not in self.app.ui_sheet_cache:
            self.app.ui_sheet_cache[theme] = pygame.image.load(str(sheet_path)).convert_alpha()
        sheet = self.app.ui_sheet_cache[theme]
        rect = pygame.Rect(int(entry["x"]), int(entry["y"]), int(entry["w"]), int(entry["h"]))
        return sheet.subsurface(rect).copy()

    def panel_surface(
        self,
        size: tuple[int, int],
        theme: str,
        sprite_id: str,
        tint: tuple[int, int, int],
        overlay_theme: str | None = None,
        overlay_sprite_id: str | None = None,
    ) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.blit(self.load_ui_sprite(theme, sprite_id, size), (0, 0))
        overlay = pygame.Surface(size, pygame.SRCALPHA)
        overlay.fill((*tint, 115))
        surface.blit(overlay, (0, 0))
        if overlay_sprite_id is not None:
            surface.blit(
                self.load_ui_sprite(overlay_theme or theme, overlay_sprite_id, size),
                (0, 0),
            )
        return surface

    def button_surface(self, button: Button) -> pygame.Surface:
        theme = button.sprite_theme or "MediavelFree"
        sprite_id = button.sprite_id or ("mf_000" if button.enabled else "ff_006")
        surface = self.panel_surface((button.rect.width, button.rect.height), theme, sprite_id, (54, 35, 20))
        outline_color = ACCENT if button.enabled else MUTED
        pygame.draw.rect(surface, outline_color, surface.get_rect(), width=2, border_radius=14)

        if button.payload.get("kind") == "equipped":
            item = button.payload.get("item")
            if item is not None:
                icon = self.load_item_sprite(item, (button.rect.width - 12, button.rect.height - 12))
                surface.blit(icon, icon.get_rect(center=surface.get_rect().center))
            else:
                label = self.app.font_small.render(button.payload.get("slot_label", ""), True, MUTED)
                surface.blit(label, label.get_rect(center=surface.get_rect().center))
            return surface

        item = button.payload.get("item")
        if item is not None and button.action.startswith(("equip", "unequip", "use_item")):
            icon = self.load_item_sprite(item, (24, 24))
            surface.blit(icon, (12, (surface.get_height() - 24) // 2))
            label = self.app.font_small.render(button.label, True, TEXT if button.enabled else MUTED)
            surface.blit(label, label.get_rect(midleft=(44, surface.get_height() // 2)))
            return surface

        label = self.app.font.render(button.label, True, TEXT if button.enabled else MUTED)
        surface.blit(label, label.get_rect(center=surface.get_rect().center))
        return surface
