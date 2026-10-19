"""
core/progression.py

Regles de progression des quetes et des titres, independantes de pygame.
"""

from __future__ import annotations

from typing import Any

from core.daily_reset import DailyResetService
from entities.companion import Companion
from party.party import Party


class ProgressionManager:
    def __init__(
        self,
        quest_catalog: dict[str, dict[str, Any]],
        title_catalog: dict[str, dict[str, Any]],
        rank_catalog: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.quest_catalog = quest_catalog
        self.title_catalog = title_catalog
        self.rank_catalog = rank_catalog or {}
        self.party: Party | None = None
        self.inventory: dict[str, dict[str, int]] = {}
        self.progression: dict[str, Any] = {}
        self.last_rank_up: str | None = None
        self.last_tier_up: dict[str, Any] | None = None

    def _quests_state(self) -> dict[str, Any]:
        quests = self.progression.setdefault("quests", {})
        quests.setdefault("active", [])
        quests.setdefault("completed", [])
        quests.setdefault("claimed", [])
        quests.setdefault("baselines", {})
        quests.setdefault("completions", {})
        quests.setdefault("daily_claimed", [])
        quests.setdefault("last_daily_reset", DailyResetService.today())
        return quests

    def reset_daily_quests(self) -> bool:
        """Rend les quetes journalieres disponibles apres un nouveau jour."""
        quests = self._quests_state()
        last_reset = quests.get("last_daily_reset")
        if not last_reset:
            quests["last_daily_reset"] = DailyResetService.today()
            return False
        if not DailyResetService.is_new_day(last_reset):
            return False
        daily_ids = {
            quest_id for quest_id, quest in self.quest_catalog.items()
            if quest.get("type", "unique") == "daily"
        }
        quests["active"] = [quest_id for quest_id in quests["active"] if quest_id not in daily_ids]
        quests["daily_claimed"] = []
        for quest_id in daily_ids:
            quests["baselines"].pop(quest_id, None)
        quests["last_daily_reset"] = DailyResetService.today()
        return True

    def normalize(self) -> None:
        """Ajoute les champs de quetes manquants des anciennes sauvegardes."""
        self._quests_state()
        self.reset_daily_quests()

    def time_until_daily_reset(self):
        return DailyResetService.time_until_reset()

    def bind(
        self,
        party: Party | None,
        inventory: dict[str, dict[str, int]],
        progression: dict[str, Any],
    ) -> None:
        self.party = party
        self.inventory = inventory
        self.progression = progression

    def condition_progress(self, condition: dict[str, Any], quest_id: str | None = None) -> tuple[int, int]:
        condition_type = str(condition.get("type", ""))
        target = int(condition.get("target", 1))
        stats = self.progression.setdefault("stats", {})
        quest = self.quest_catalog.get(quest_id or "", {})
        relative = quest.get("type", "unique") in ("repeatable", "daily") and quest_id is not None
        baseline = self._quests_state().get("baselines", {}).get(quest_id or "", {})
        if condition_type == "victories":
            current = int(stats.get("victories", 0)) - (int(baseline.get(condition_type, 0)) if relative else 0)
        elif condition_type == "gold_earned":
            current = int(stats.get("gold_earned", 0)) - (int(baseline.get(condition_type, 0)) if relative else 0)
        elif condition_type == "quests_completed":
            current = int(stats.get("quests_completed", 0)) - (int(baseline.get(condition_type, 0)) if relative else 0)
        elif condition_type == "level":
            current = int(getattr(self.party.leader, "level", 0)) if self.party else 0
        elif condition_type == "defeat_enemy":
            defeated = stats.get("enemies_defeated", {})
            current = int(defeated.get(str(condition.get("enemy_id", "")), 0))
        elif condition_type == "min_rank":
            current = self._rank_index(self.current_rank_id())
            target = self._rank_index(str(condition.get("rank", "iron")))
        else:
            current = 0
        return min(current, target), target

    def _rank_index(self, rank_id: str) -> int:
        return next((index for index, current in enumerate(self.rank_catalog) if current == rank_id), 0)

    def current_rank_id(self) -> str:
        return str(getattr(self.party.leader, "rank", "iron")) if self.party and self.party.leader else "iron"

    def rank_at_least(self, rank_id: str | None) -> bool:
        return self._rank_index(self.current_rank_id()) >= self._rank_index(str(rank_id or "iron"))

    def _evaluation_visible(self, quest: dict[str, Any]) -> bool:
        if quest.get("class_trial"):
            leader = self.party.leader if self.party else None
            if leader is None or leader.class_id != quest.get("class_id"):
                return False
            return int(leader.tier) + 1 == int(quest.get("tier", 1))
        rank_id = quest.get("evaluation_rank")
        if not rank_id:
            return True
        if self.party is None or self.party.leader is None:
            return False
        rank_index = self._rank_index(str(rank_id))
        current_index = self._rank_index(self.current_rank_id())
        rank = self.rank_catalog.get(str(rank_id), {})
        return rank_index == current_index + 1 and int(getattr(self.party.leader, "level", 0)) >= int(rank.get("min_level", 1))

    def conditions_met(self, conditions: list[dict[str, Any]] | dict[str, Any], quest_id: str | None = None) -> bool:
        if isinstance(conditions, dict):
            conditions = [conditions]
        return all(
            current >= target
            for current, target in (self.condition_progress(condition, quest_id) for condition in conditions)
        )

    def quest_status(self, quest_id: str) -> str:
        self.normalize()
        quests = self._quests_state()
        quest = self.quest_catalog.get(quest_id, {})
        if not self._evaluation_visible(quest):
            return "hidden"
        quest_type = quest.get("type", "unique")
        if quest_type == "unique" and quest_id in quests.get("claimed", []):
            return "claimed"
        if quest_type == "daily" and quest_id in quests.get("daily_claimed", []):
            return "claimed"
        quest = self.quest_catalog.get(quest_id, {})
        if quest_id in quests.get("active", []):
            return "claimable" if self.conditions_met(quest.get("conditions", {}), quest_id) else "active"
        return "available"

    def accept_quest(self, quest_id: str) -> bool:
        self.normalize()
        if self.quest_status(quest_id) != "available":
            return False
        quest = self.quest_catalog.get(quest_id, {})
        quests = self._quests_state()
        quests["active"].append(quest_id)
        if quest.get("type", "unique") in ("repeatable", "daily"):
            stats = self.progression.setdefault("stats", {})
            conditions = quest.get("conditions", {})
            conditions = conditions if isinstance(conditions, list) else [conditions]
            quests["baselines"][quest_id] = {
                condition["type"]: int(stats.get(condition["type"], 0))
                for condition in conditions
                if condition.get("type") != "level"
            }
        return True

    def claim_quest(self, quest_id: str) -> str | None:
        self.normalize()
        quest = self.quest_catalog.get(quest_id)
        if quest is None or self.quest_status(quest_id) != "claimable":
            return None

        rewards = quest.get("rewards", {})
        leader = self.party.leader if self.party else None
        self.last_rank_up = None
        self.last_tier_up = None
        if leader is not None:
            leader.gold += int(rewards.get("gold", 0))
            if rewards.get("xp"):
                leader.gain_xp(int(rewards["xp"]))
        for category in ("items", "weapons", "armors", "pets"):
            self.inventory.setdefault(category, {})
            for item_id, quantity in rewards.get(category, {}).items():
                self.inventory[category][item_id] = self.inventory[category].get(item_id, 0) + int(quantity)
        rank_up = rewards.get("rank_up")
        if leader is not None and isinstance(rank_up, str) and rank_up in self.rank_catalog:
            leader.rank = rank_up
            self.last_rank_up = rank_up

        tier_up = rewards.get("tier_up")
        if leader is not None and isinstance(tier_up, dict):
            if tier_up.get("class_id") == leader.class_id:
                old_tier = leader.tier
                leader.set_class(leader.class_id, int(tier_up.get("tier", old_tier)), preserve_hp_ratio=True)
                self.last_tier_up = {
                    "class_id": leader.class_id,
                    "old_tier": old_tier,
                    "new_tier": leader.tier,
                }

        quests_state = self.progression["quests"]
        quests_state["active"].remove(quest_id)
        quest_type = quest.get("type", "unique")
        quests_state.setdefault("completed", []).append(quest_id)
        if quest_type == "unique":
            quests_state.setdefault("claimed", []).append(quest_id)
        elif quest_type == "daily":
            quests_state.setdefault("daily_claimed", []).append(quest_id)
        elif quest_type == "repeatable":
            completions = quests_state.setdefault("completions", {})
            completions[quest_id] = int(completions.get(quest_id, 0)) + 1
        quests_state.setdefault("baselines", {}).pop(quest_id, None)
        self.progression["stats"]["quests_completed"] = int(self.progression["stats"].get("quests_completed", 0)) + 1
        return self.update_titles()

    def update_titles(self) -> str | None:
        titles = self.progression.setdefault("titles", {})
        feedback = None
        for title in self.title_catalog.values():
            title_id = str(title["id"])
            previous_state = titles.get(title_id, {})
            conditions = title.get("conditions", {})
            conditions = conditions if isinstance(conditions, list) else [conditions]
            progress = [self.condition_progress(condition) for condition in conditions]
            titles[title_id] = {
                "progress": [{"current": current, "target": target} for current, target in progress],
                "unlocked": all(current >= target for current, target in progress),
                "reward_claimed": bool(previous_state.get("reward_claimed", False)),
            }
            reward_feedback = self._claim_title_reward(title, titles[title_id])
            if reward_feedback is not None:
                feedback = reward_feedback
        return feedback

    def _claim_title_reward(self, title: dict[str, Any], title_state: dict[str, Any]) -> str | None:
        if not title_state.get("unlocked") or title_state.get("reward_claimed"):
            return None
        reward = title.get("reward", {})
        if reward.get("type") != "companion" or self.party is None:
            return None

        companion_id = str(reward.get("id", title.get("id", "companion")))
        if any(getattr(companion, "reward_id", None) == companion_id for companion in self.party.companions):
            title_state["reward_claimed"] = True
            return None

        companion = Companion(
            name=str(reward.get("name", "Compagnon")),
            max_hp=int(reward.get("max_hp", 20)),
            attack=int(reward.get("attack", 3)),
            defense=int(reward.get("defense", 1)),
            speed=int(reward.get("speed", 1)),
            role=str(reward.get("role", "attacker")),
            class_id=str(reward.get("class_id", "warrior")),
            tier=int(reward.get("tier", 1)),
        )
        companion.reward_id = companion_id
        self.party.recruit(companion)
        title_state["reward_claimed"] = True
        return f"{companion.name} rejoint votre groupe."
