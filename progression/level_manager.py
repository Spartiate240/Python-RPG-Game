"""Gestion des niveaux et de la table d'experience."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


XP_TABLE_PATH = Path(__file__).resolve().parent / "xp_table.json"


class LevelManager:
    """Applique l'XP, les paliers et les bonus de niveau aux allies."""

    def __init__(self, xp_table_path: Path = XP_TABLE_PATH) -> None:
        data = json.loads(xp_table_path.read_text(encoding="utf-8"))
        self.thresholds = {
            int(entry["level"]): int(entry["required_xp"])
            for entry in data
            if isinstance(entry, dict) and "level" in entry and "required_xp" in entry
        }

    def add_xp(self, ally: Any, amount: int) -> int:
        ally.xp += max(0, int(amount))
        levels_gained = 0
        while self.can_level_up(ally):
            self._level_up(ally)
            levels_gained += 1
        return levels_gained

    def can_level_up(self, ally: Any) -> bool:
        next_level = int(ally.level) + 1
        threshold = self.thresholds.get(next_level)
        return threshold is not None and int(ally.xp) >= threshold

    @staticmethod
    def _level_up(ally: Any) -> None:
        ally.level += 1
        ally.max_hp += 2
        ally.hp = ally.max_hp
        ally.attack += 1
        ally.defense += 1
