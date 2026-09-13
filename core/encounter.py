"""Creation des rencontres, independante de pygame."""

from __future__ import annotations

import random

from core.battle import Battle
from core.catalog import Catalogs
from entities.enemy import Enemy
from party.party import Party


class EncounterService:
    """Construit un combat a partir de la zone courante."""

    def __init__(self, catalogs: Catalogs) -> None:
        self.catalogs = catalogs

    def start_battle(self, party: Party, location: str | None) -> Battle:
        zone = self.catalogs.zone_for_id(location) or {}
        enemy_ids = [
            enemy_id
            for enemy_id in zone.get("enemies", ["goblin"])
            if enemy_id in self.catalogs.enemies
        ]
        if not enemy_ids:
            enemy_ids = ["goblin"]
        enemy_id = random.choice(enemy_ids)
        enemy = Enemy.from_id(enemy_id)
        return Battle(
            party,
            [enemy],
            [self.catalogs.enemies.get(enemy_id, {})],
            self.catalogs.skills,
        )