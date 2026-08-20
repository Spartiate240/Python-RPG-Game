"""
entities/enemy.py

Ennemi "jetable" : pas de progression, pas d'inventaire.
Instancié à chaque combat depuis data/enemies.json.
"""

from __future__ import annotations
import json
import random
from pathlib import Path

from entities.combatant import Combatant, Action

ENEMIES_JSON = Path("data/enemies.json")


class Enemy(Combatant):
    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        speed: int,
        xp_reward: int = 0,
        gold_reward: int = 0,
        loot_table: list[dict] | None = None,
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed)
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.loot_table = loot_table or []  # [{"item_id": "...", "chance": 0.3}, ...]

    # ---- Chargement depuis JSON -----------------------------------
    @classmethod
    def from_id(cls, enemy_id: str) -> "Enemy":
        with ENEMIES_JSON.open(encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            payload = data[enemy_id]
        else:
            payload = next((entry for entry in data if entry.get("id") == enemy_id), None)
            if payload is None:
                raise KeyError(f"Unknown enemy id: {enemy_id}")

        loot_table = payload.get("loot_table")
        if loot_table is None:
            loot_table = [
                {"item_id": item_id, "chance": amount / 100}
                for item_id, amount in payload.get("drops", {}).items()
            ]

        return cls(
            name=payload["name"],
            max_hp=payload.get("hp", payload.get("health")),
            attack=payload.get("attack", payload.get("damage")),
            defense=payload["defense"],
            speed=payload["speed"],
            xp_reward=payload.get("xp_reward", payload.get("given_exp", 0)),
            gold_reward=payload.get("gold_reward", 0),
            loot_table=loot_table,
        )

    def roll_loot(self) -> list[str]:
        return [
            drop["item_id"]
            for drop in self.loot_table
            if random.random() < drop.get("chance", 0)
        ]

    # ---- IA basique -------------------------------------------------
    def choose_action(self, allies: list[Combatant], enemies: list[Combatant]) -> Action:
        living_targets = [enemy for enemy in enemies if enemy.is_alive()]
        if not living_targets:
            return Action("defend")
        target = random.choice(living_targets)
        return Action("attack", target=target)
