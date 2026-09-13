"""Ecran de boutique."""

from __future__ import annotations

from typing import Any

import pygame

from ui.theme import ACCENT, ACCENT_2, MUTED, PANEL, SUCCESS, TEXT
from ui.widgets import Button


SHOP_PANEL_RECT = pygame.Rect(60, 70, 1160, 580)
SHOP_BACK_BUTTON_RECT = pygame.Rect(1075, 610, 130, 56)
SHOP_MERCHANT_BUTTON_RECT = pygame.Rect(150, 205, 980, 70)
SHOP_ITEM_BUTTON_X = 130
SHOP_ITEM_BUTTON_W = 700
SHOP_ITEM_BUTTON_H = 48
SHOP_ITEM_START_Y = 190
SHOP_ITEM_ROW_GAP = 58


class ShopScreen:
    """Construit le rendu de la boutique."""

    @staticmethod
    def selected_merchant(app: Any) -> dict[str, Any] | None:
        if app.selected_merchant_id is None:
            return None
        return app.merchant_catalog.get(app.selected_merchant_id)

    def _merchant_item_buttons(self, app: Any) -> list[Button]:
        if self.selected_merchant(app) is None:
            return []

        buttons: list[Button] = []
        row_index = 0
        stock = app.merchant_stock.get(app.selected_merchant_id or "", {})
        for category, entries in stock.items():
            for item_id, values in entries.items():
                item = app.catalogs.resolve_item(item_id)
                quantity = int(values.get("quantity", 0))
                cost = int(values.get("cost", 0))
                label = item.get("name", item_id) if item else f"Objet inconnu ({item_id})"
                buttons.append(
                    Button(
                        f"{label}  —  {cost} or  —  x{quantity}",
                        pygame.Rect(SHOP_ITEM_BUTTON_X, SHOP_ITEM_START_Y + row_index * SHOP_ITEM_ROW_GAP, SHOP_ITEM_BUTTON_W, SHOP_ITEM_BUTTON_H),
                        f"buy:{category}:{item_id}",
                        payload={"item": item, "category": category, "item_id": item_id, "cost": cost},
                        enabled=item is not None and quantity > 0,
                    )
                )
                row_index += 1
        return buttons

    def buttons(self, app: Any) -> list[Button]:
        buttons = [Button("Retour", SHOP_BACK_BUTTON_RECT, "back")]
        if app.selected_merchant_id is None:
            for index, merchant in enumerate(app.merchant_catalog.values()):
                buttons.append(
                    Button(
                        str(merchant.get("name", merchant["id"])),
                        pygame.Rect(SHOP_MERCHANT_BUTTON_RECT.x, SHOP_MERCHANT_BUTTON_RECT.y + index * 86, SHOP_MERCHANT_BUTTON_RECT.w, SHOP_MERCHANT_BUTTON_RECT.h),
                        f"merchant:{merchant['id']}",
                    )
                )
        else:
            buttons.append(Button("Changer de marchand", pygame.Rect(760, 545, 280, 48), "merchant_list"))
            buttons.extend(self._merchant_item_buttons(app))
        return buttons

    def render(self, app: Any) -> None:
        app._draw_panel(SHOP_PANEL_RECT, PANEL)
        app._draw_text("Boutique", (100, 110), app.font_big, ACCENT)
        merchant = self.selected_merchant(app)
        if merchant is None:
            app._draw_text("Choisis ton marchand.", (100, 170), app.font, MUTED)
            for index, merchant_entry in enumerate(app.merchant_catalog.values()):
                app._draw_text(
                    str(merchant_entry.get("description", "")),
                    (175, 282 + index * 86),
                    app.font_small,
                    MUTED,
                )
        else:
            gold = app.party.leader.gold if app.party and app.party.leader else 0
            app._draw_text(str(merchant.get("name", "Marchand")), (100, 165), app.font, ACCENT_2)
            app._draw_text(str(merchant.get("description", "")), (100, 200), app.font_small, MUTED)
            app._draw_text(f"Or: {gold}", (900, 115), app.font, SUCCESS)
            app._draw_text("Stock", (100, 150), app.font, ACCENT)
            app._draw_text(
                "Les références absentes des catalogues sont indisponibles.",
                (100, 510),
                app.font_small,
                MUTED,
            )
            if app.status_feedback:
                app._draw_text(app.status_feedback, (100, 565), app.font_small, TEXT)
        app._draw_buttons(self.buttons(app))
