"""
core/battle.py

Logique des combats, indépendante de pygame.
"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from entities.combatant import Combatant
from entities.enemy import Enemy
from entities.player import Player
from party.party import Party


ROOT_DIR = Path(__file__).resolve().parents[1]


class Battle:
    def __init__(self, party: Party, enemies: list[Enemy], enemy_meta: list[dict]) -> None:
        self.party = party
        self.enemies = enemies
        self.enemy_meta = enemy_meta
        self.turn_order: list[Combatant] = []
        self.turn_index = 0
        self.messages: deque[str] = deque(maxlen=7)
        self.result: str | None = None
        self._rebuild_turn_order()
        self._auto_play_until_player()

    def _rebuild_turn_order(self) -> None:
        combatants = [*self.party.active_members(), *self.enemies]
        self.turn_order = sorted(combatants, key=lambda combatant: combatant.speed, reverse=True)
        self.turn_index = 0

    def _current_actor(self) -> Combatant | None:
        if self.result is not None:
            return None
        if not self.turn_order:
            self._rebuild_turn_order()
        if not self.turn_order:
            return None
        if self.turn_index >= len(self.turn_order):
            self._rebuild_turn_order()
        if not self.turn_order:
            return None
        while self.turn_index < len(self.turn_order) and not self.turn_order[self.turn_index].is_alive():
            self.turn_index += 1
            if self.turn_index >= len(self.turn_order):
                self._rebuild_turn_order()
                if not self.turn_order:
                    return None
        return self.turn_order[self.turn_index]

    def _advance_turn(self) -> None:
        self.turn_index += 1
        if self.turn_index >= len(self.turn_order):
            self._rebuild_turn_order()

    def _attack_value(self, actor: Combatant) -> int:
        return int(getattr(actor, "total_attack", actor.attack))

    def _defense_value(self, target: Combatant) -> int:
        return int(getattr(target, "total_defense", target.defense))

    def _log(self, message: str) -> None:
        self.messages.append(message)

    def _check_outcome(self) -> None:
        if not any(member.is_alive() for member in self.party.active_members()):
            self.result = "defeat"
            self._log("Le groupe a été vaincu.")
            return
        if not any(enemy.is_alive() for enemy in self.enemies):
            self.result = "victory"
            total_xp = sum(enemy.xp_reward for enemy in self.enemies)
            total_gold = sum(enemy.gold_reward for enemy in self.enemies)
            for member in self.party.active_members():
                if hasattr(member, "gain_xp"):
                    member.gain_xp(total_xp)
            if self.party.leader is not None:
                self.party.leader.gold += total_gold
            self._log(f"Victoire. +{total_xp} XP, +{total_gold} or.")

    def _sides_for(self, combatant: Combatant) -> tuple[list[Combatant], list[Combatant]]:
        if combatant in self.enemies:
            return self.enemies, list(self.party.active_members())
        return list(self.party.active_members()), self.enemies

    def _resolve_attack(self, actor: Combatant, target: Combatant) -> None:
        damage = max(1, self._attack_value(actor) - self._defense_value(target))
        dealt = target.take_damage(damage)
        self._log(f"{actor.name} attaque {target.name} pour {dealt} dégâts.")
        self._check_outcome()

    def _auto_play_until_player(self) -> None:
        while self.result is None:
            actor = self._current_actor()
            if actor is None:
                return
            if not actor.is_alive():
                self._advance_turn()
                continue
            if isinstance(actor, Player):
                return

            allies, enemies = self._sides_for(actor)
            action = actor.choose_action(allies, enemies)
            if action.kind == "attack" and action.target is not None:
                self._resolve_attack(actor, action.target)
            elif action.kind == "defend":
                self._log(f"{actor.name} se met en garde.")
            else:
                self._log(f"{actor.name} passe son tour.")
            if self.result is not None:
                return
            self._advance_turn()

    def player_attack(self, target: Combatant) -> None:
        leader = self.party.leader
        if leader is None or not leader.is_alive() or self.result is not None:
            return
        self._resolve_attack(leader, target)
        if self.result is None:
            self._advance_turn()
            self._auto_play_until_player()

    def flee(self) -> None:
        if self.result is None:
            self.result = "flee"
            self._log("Le groupe prend la fuite.")

    @property
    def current_actor(self) -> Combatant | None:
        return self._current_actor()

    @property
    def enemy_sprite_path(self) -> str | None:
        for meta in self.enemy_meta:
            sprite = meta.get("sprite")
            if sprite:
                return str(ROOT_DIR / "data" / sprite)
        return None
