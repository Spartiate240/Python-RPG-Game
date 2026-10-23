"""Regles metier de l'extraction des ombres."""

from __future__ import annotations

import random
from typing import Any

MIN_EXTRACTION_CHANCE = 10
MAX_EXTRACTION_CHANCE = 85
EXTRACTION_ATTEMPTS = 3


def rank_order(shadow_ranks: dict[str, Any]) -> list[str]:
    return list(shadow_ranks.get("ranks", {}).keys())


def rank_index(shadow_ranks: dict[str, Any], rank_id: str) -> int:
    try:
        return rank_order(shadow_ranks).index(rank_id)
    except ValueError:
        return 0


def next_rank_id(shadow_ranks: dict[str, Any], rank_id: str) -> str | None:
    ranks = rank_order(shadow_ranks)
    index = rank_index(shadow_ranks, rank_id)
    return ranks[index + 1] if index + 1 < len(ranks) else None


def shadow_rank_cost(shadow: Any, shadow_ranks: dict[str, Any]) -> dict[str, Any] | None:
    next_rank = next_rank_id(shadow_ranks, getattr(shadow, "rank_id", "soldier"))
    return shadow_ranks.get("costs", {}).get(getattr(shadow, "enemy_id", ""), {}).get(next_rank) if next_rank else None


def shadow_rank_block_reason(shadow: Any, necromancer: Any, inventory: dict[str, dict[str, int]], shadow_ranks: dict[str, Any]) -> str | None:
    next_rank = next_rank_id(shadow_ranks, getattr(shadow, "rank_id", "soldier"))
    if next_rank is None:
        return "Rang maximal atteint."
    max_rank = str(getattr(necromancer, "tier_data", {}).get("max_shadow_rank", "soldier"))
    if rank_index(shadow_ranks, next_rank) > rank_index(shadow_ranks, max_rank):
        return "Le tier du nécromancien est insuffisant."
    cost = shadow_rank_cost(shadow, shadow_ranks) or {}
    if int(getattr(shadow, "level", 1)) < int(cost.get("min_level", 1)):
        return f"Niveau {cost.get('min_level', 1)} requis."
    items = inventory.get("items", {})
    for item_id, required in cost.get("materials", {}).items():
        if int(items.get(item_id, 0)) < int(required):
            return "Matériaux insuffisants."
    essence = int(items.get("shadow_essence", 0))
    if essence < int(cost.get("shadow_essence", 0)):
        return "Essence d'ombre insuffisante."
    return None


def promote_shadow(shadow: Any, necromancer: Any, inventory: dict[str, dict[str, int]], shadow_ranks: dict[str, Any]) -> tuple[bool, str]:
    reason = shadow_rank_block_reason(shadow, necromancer, inventory, shadow_ranks)
    if reason is not None:
        return False, reason
    next_rank = next_rank_id(shadow_ranks, shadow.rank_id)
    cost = shadow_rank_cost(shadow, shadow_ranks) or {}
    items = inventory.setdefault("items", {})
    for item_id, required in cost.get("materials", {}).items():
        items[item_id] = int(items.get(item_id, 0)) - int(required)
        if items[item_id] <= 0:
            items.pop(item_id, None)
    essence_cost = int(cost.get("shadow_essence", 0))
    items["shadow_essence"] = int(items.get("shadow_essence", 0)) - essence_cost
    if items["shadow_essence"] <= 0:
        items.pop("shadow_essence", None)
    shadow.set_rank(next_rank, shadow_ranks["ranks"][next_rank])
    return True, next_rank


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