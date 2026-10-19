"""Ombre extraite d'un ennemi vaincu."""

from __future__ import annotations

from typing import Any

from entities.companion import Companion


class Shadow(Companion):
    def __init__(self, enemy_id: str, sprite_path: str | None = None, **kwargs: Any) -> None:
        super().__init__(role="attacker", **kwargs)
        self.enemy_id = enemy_id
        self.sprite_path = sprite_path
        self._dispersed = False

    @classmethod
    def from_enemy_data(cls, enemy_id: str, data: dict[str, Any], level: int | None = None, xp: int = 0) -> "Shadow":
        return cls(
            enemy_id=enemy_id,
            sprite_path=data.get("sprite"),
            name=f"Ombre de {data.get('name', enemy_id)}",
            max_hp=int(data.get("health", data.get("hp", 1))),
            attack=int(data.get("damage", data.get("attack", 1))),
            defense=int(data.get("defense", 0)),
            speed=int(data.get("speed", 1)),
            level=int(level if level is not None else data.get("level", 1)),
            xp=int(xp),
            class_id="shadow",
            tier=1,
        )

    def to_shadow_dict(self) -> dict[str, Any]:
        return {"enemy_id": self.enemy_id, "level": self.level, "xp": self.xp}

    def restore_after_battle(self) -> None:
        self.hp = self.max_hp
        self._dispersed = False