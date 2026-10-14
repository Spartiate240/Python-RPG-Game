"""
core/battle.py

Logique des combats, indépendante de pygame.
"""

from __future__ import annotations

from collections import deque
import random
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from entities.combatant import Combatant
from entities.enemy import Enemy
from entities.player import Player
from party.party import Party


ROOT_DIR = Path(__file__).resolve().parents[1]


class Battle:
    def __init__(
        self,
        party: Party,
        enemies: list[Enemy],
        enemy_meta: list[dict],
        skill_catalog: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.party = party
        self.enemies = enemies
        self.enemy_meta = enemy_meta
        self.skill_catalog = skill_catalog or {}
        self.turn_order: list[Combatant] = []
        self.turn_index = 0
        self.messages: deque[str] = deque(maxlen=7)
        self.result: str | None = None
        self.loot: list[str] = []
        self.total_xp = 0
        self.total_gold = 0
        self.loot_collected = False
        self._rebuild_turn_order()
        self._auto_play_until_player()

    def _rebuild_turn_order(self) -> None:
        combatants = [*self.party.active_members(), *self.enemies]
        self.turn_order = sorted(combatants, key=lambda combatant: getattr(combatant, "total_speed", combatant.speed), reverse=True)
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

    def log_message(self, message: str) -> None:
        """Ajoute au journal un événement géré par un service externe."""
        self._log(message)

    def _check_outcome(self) -> None:
        if self.result is not None:
            return
        if not any(member.is_alive() for member in self.party.active_members()):
            self.result = "defeat"
            self._log("Le groupe a été vaincu.")
            return
        if not any(enemy.is_alive() for enemy in self.enemies):
            self.result = "victory"
            total_xp = sum(enemy.xp_reward for enemy in self.enemies)
            self.total_xp = total_xp
            total_gold = sum(enemy.roll_gold() for enemy in self.enemies)
            self.total_gold = total_gold
            for member in self.party.active_members():
                if hasattr(member, "gain_xp"):
                    member.gain_xp(total_xp)
            if self.party.leader is not None:
                self.party.leader.gold += total_gold
            self.loot = [item_id for enemy in self.enemies for item_id in enemy.roll_loot()]
            self._log(f"Victoire. +{total_xp} XP, +{total_gold} or.")

    def _apply_turn_start(self, actor: Combatant) -> None:
        for passive in getattr(actor, "class_passives", lambda _trigger: [])("on_turn_start"):
            if passive.get("effect") == "regen_percent_health":
                restored = actor.heal(max(1, int(actor.max_hp * float(passive.get("value", 0)))))
                if restored:
                    self._log(f"{actor.name} récupère {restored} PV.")

    def _sides_for(self, combatant: Combatant) -> tuple[list[Combatant], list[Combatant]]:
        if combatant in self.enemies:
            return self.enemies, list(self.party.active_members())
        return list(self.party.active_members()), self.enemies

    def _resolve_attack(self, actor: Combatant, target: Combatant, trigger_passive: bool = True) -> None:
        damage = max(1, self._attack_value(actor) - self._defense_value(target))
        dealt = target.take_damage(damage)
        self._log(f"{actor.name} attaque {target.name} pour {dealt} dégâts.")
        if not target.is_alive():
            self._log(f"{target.name} est vaincu.")
        self._check_outcome()
        if trigger_passive and self.result is None and target.is_alive():
            for passive in getattr(actor, "class_passives", lambda _trigger: [])("on_attack"):
                if passive.get("effect") == "extra_attack" and random.random() < float(passive.get("chance", 0)):
                    self._log(f"{actor.name} obtient une attaque supplémentaire.")
                    self._resolve_attack(actor, target, trigger_passive=False)
                    break

    def available_skills(self, actor: Combatant) -> list[SimpleNamespace]:
        """Retourne les skills déclarés par les armes équipées de l'acteur."""
        skills: list[SimpleNamespace] = []
        for weapon_name in ("weapon_primary", "weapon_secondary"):
            weapon = getattr(actor, weapon_name, None)
            skill_ids = weapon.get("skills", []) if isinstance(weapon, dict) else getattr(weapon, "skills", [])
            for skill_id in skill_ids or []:
                skill_data = self.skill_catalog.get(skill_id)
                if skill_data is not None:
                    skills.append(SimpleNamespace(**skill_data))
        return skills

    def _resolve_skill(self, actor: Combatant, target: Combatant | None, skill: Any) -> None:
        skill_type = getattr(skill, "type", "attack")
        if skill_type == "defense":
            bonus = int(getattr(skill, "defense", 0))
            actor.defense += bonus
            self._log(f"{actor.name} utilise {skill.name} et gagne {bonus} défense.")
            return

        if target is None or not target.is_alive():
            return
        damage = max(1, int(getattr(skill, "damage", 0)) + self._attack_value(actor) - self._defense_value(target))
        dealt = target.take_damage(damage)
        self._log(f"{actor.name} utilise {skill.name} sur {target.name} pour {dealt} dégâts.")
        if not target.is_alive():
            self._log(f"{target.name} est vaincu.")
        self._check_outcome()

    def _finish_player_action(self) -> None:
        if self.result is None:
            self._advance_turn()
            self._auto_play_until_player()

    def _auto_play_until_player(self) -> None:
        while self.result is None:
            actor = self._current_actor()
            if actor is None:
                return
            if not actor.is_alive():
                self._advance_turn()
                continue
            self._apply_turn_start(actor)
            if isinstance(actor, Player):
                return

            allies, enemies = self._sides_for(actor)
            action = actor.choose_action(allies, enemies)
            if action.kind == "attack" and action.target is not None:
                self._resolve_attack(actor, action.target)
            elif action.kind == "skill":
                self._resolve_skill(actor, action.target, action.payload.get("skill"))
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
        self._finish_player_action()

    def player_skill(self, skill_id: str, target: Combatant | None = None) -> None:
        leader = self.party.leader
        if leader is None or not leader.is_alive() or self.result is not None:
            return
        skill = next((item for item in self.available_skills(leader) if item.id == skill_id), None)
        if skill is None:
            return
        if getattr(skill, "target", "single_enemy") == "all_enemies":
            for enemy in self.enemies:
                if enemy.is_alive():
                    self._resolve_skill(leader, enemy, skill)
        else:
            self._resolve_skill(leader, target, skill)
        self._finish_player_action()

    def finish_player_action(self) -> None:
        """Avance le tour après une action validée par un service externe."""
        self._finish_player_action()

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
