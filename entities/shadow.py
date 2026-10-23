"""Ombre extraite d'un ennemi vaincu."""

from __future__ import annotations

from typing import Any

from entities.companion import Companion


class Shadow(Companion):
    def __init__(self, enemy_id: str, sprite_path: str | None = None, rank_id: str = "soldier", rank_data: dict[str, Any] | None = None, shadow_growth: dict[str, int] | None = None, **kwargs: Any) -> None:
        base_stats = kwargs.pop("base_stats", {})
        super().__init__(role="attacker", **kwargs)
        self.enemy_id = enemy_id
        self.sprite_path = sprite_path
        self.rank_id = rank_id or "soldier"
        self.rank_data = rank_data or {"id": self.rank_id, "stat_multiplier": 1.0}
        self.shadow_base_stats = {key: int(value) for key, value in base_stats.items()}
        self.shadow_growth = {key: int(value) for key, value in (shadow_growth or {}).items()}
        self._dispersed = False

    @classmethod
    def from_enemy_data(cls, enemy_id: str, data: dict[str, Any], level: int | None = None, xp: int = 0, rank_id: str = "soldier", rank_data: dict[str, Any] | None = None) -> "Shadow":
        base_stats = {
            "max_hp": int(data.get("health", data.get("hp", 1))),
            "attack": int(data.get("damage", data.get("attack", 1))),
            "defense": int(data.get("defense", 0)),
            "speed": int(data.get("speed", 1)),
        }
        return cls(
            enemy_id=enemy_id,
            sprite_path=data.get("sprite"),
            name=f"Ombre de {data.get('name', enemy_id)}",
            max_hp=base_stats["max_hp"], attack=base_stats["attack"], defense=base_stats["defense"], speed=base_stats["speed"],
            level=int(level if level is not None else data.get("level", 1)),
            xp=int(xp),
            class_id="shadow",
            tier=1,
            rank_id=rank_id,
            rank_data=rank_data,
            shadow_growth=data.get("shadow_growth", {"max_hp": 2, "attack": 1, "defense": 1, "speed": 0}),
            base_stats=base_stats,
        )

    def _derived_stat(self, stat: str) -> int:
        base = self.shadow_base_stats.get(stat, self._fallback_stats.get(stat, 0))
        growth = self.shadow_growth.get(stat, 0)
        multiplier = float(self.rank_data.get("stat_multiplier", 1.0))
        return int(round(base + growth * (self.level - 1) * multiplier))

    def set_rank(self, rank_id: str, rank_data: dict[str, Any]) -> None:
        self.rank_id = rank_id
        self.rank_data = rank_data
        self.refresh_stats()

    def to_shadow_dict(self) -> dict[str, Any]:
        return {"enemy_id": self.enemy_id, "level": self.level, "xp": self.xp, "rank_id": self.rank_id}

    def restore_after_battle(self) -> None:
        self.hp = self.max_hp
        self._dispersed = False