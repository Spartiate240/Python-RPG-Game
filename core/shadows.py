"""Regles metier de l'extraction des ombres."""

from __future__ import annotations

import random
from typing import Any

MIN_EXTRACTION_CHANCE = 10
MAX_EXTRACTION_CHANCE = 85
EXTRACTION_ATTEMPTS = 3


def extraction_chance(necromancer: Any, enemy: Any, difficulty: int) -> int:
    level_gap = int(getattr(necromancer, "level", 1)) - int(getattr(enemy, "level", 1))
    chance = 70 - int(difficulty) + level_gap * 8
    return max(MIN_EXTRACTION_CHANCE, min(MAX_EXTRACTION_CHANCE, chance))


def attempt_extraction(necromancer: Any, enemy: Any, difficulty: int, rng: Any = random) -> bool:
    return rng.random() < extraction_chance(necromancer, enemy, difficulty) / 100


def can_extract(party: Any) -> bool:
    return any(
        getattr(member, "class_id", None) == "necromancer"
        and bool(getattr(member, "tier_data", {}).get("can_extract", False))
        for member in getattr(party, "members", [])
    )