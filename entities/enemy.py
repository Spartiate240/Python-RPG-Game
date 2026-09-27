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
        gold_table: list[dict] | None = None,
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed)
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.loot_table = loot_table or []
        self.gold_table = gold_table or []

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

        drops = payload.get("drops", {})
        loot_table: list[dict] = []
        gold_table: list[dict] = []
        for item_id, value in drops.items():
            if item_id == "gold_coin" and not isinstance(value, dict):
                quantity = int(value)
                chance = 1
            elif isinstance(value, dict):
                quantity = int(value.get("quantity", 1))
                chance = float(value.get("chance", 1))
            else:
                quantity = 1
                chance = float(value) / 100
            drop = {"quantity": max(0, quantity), "chance": max(0, min(1, chance))}
            if item_id == "gold_coin":
                gold_table.append(drop)
            else:
                loot_table.append({"item_id": item_id, **drop})

        if payload.get("loot_table") is not None:
            loot_table = payload["loot_table"]
        gold_reward = int(payload.get("gold_reward", 0))

        return cls(
            name=payload["name"],
            max_hp=payload.get("hp", payload.get("health")),
            attack=payload.get("attack", payload.get("damage")),
            defense=payload["defense"],
            speed=payload["speed"],
            xp_reward=payload.get("xp_reward", payload.get("given_exp", 0)),
            gold_reward=gold_reward,
            loot_table=loot_table,
            gold_table=gold_table,
        )

    def roll_loot(self) -> list[str]:
        return [
            drop["item_id"]
            for drop in self.loot_table
            for _ in range(int(drop.get("quantity", 1)))
            if random.random() < float(drop.get("chance", 0))
        ]

    def roll_gold(self) -> int:
        return self.gold_reward + sum(
            int(drop.get("quantity", 0))
            for drop in self.gold_table
            if random.random() < float(drop.get("chance", 0))
        )

    # ---- IA basique -------------------------------------------------
    def choose_action(self, allies: list[Combatant], enemies: list[Combatant]) -> Action:
        living_targets = [enemy for enemy in enemies if enemy.is_alive()]
        if not living_targets:
            return Action("defend")
        target = random.choice(living_targets)
        return Action("attack", target=target)
