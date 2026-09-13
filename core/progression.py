"""
core/progression.py

Regles de progression des quetes et des titres, independantes de pygame.
"""

from __future__ import annotations

from typing import Any

from entities.companion import Companion
from party.party import Party


class ProgressionManager:
    def __init__(self, quest_catalog: dict[str, dict[str, Any]], title_catalog: dict[str, dict[str, Any]]) -> None:
        self.quest_catalog = quest_catalog
        self.title_catalog = title_catalog
        self.party: Party | None = None
        self.inventory: dict[str, dict[str, int]] = {}
        self.progression: dict[str, Any] = {}

    def bind(
        self,
        party: Party | None,
        inventory: dict[str, dict[str, int]],
        progression: dict[str, Any],
    ) -> None:
        self.party = party
        self.inventory = inventory
        self.progression = progression

    def condition_progress(self, condition: dict[str, Any]) -> tuple[int, int]:
        condition_type = str(condition.get("type", ""))
        target = int(condition.get("target", 1))
        stats = self.progression.setdefault("stats", {})
        if condition_type == "victories":
            current = int(stats.get("victories", 0))
        elif condition_type == "gold_earned":
            current = int(stats.get("gold_earned", 0))
        elif condition_type == "quests_completed":
            current = int(stats.get("quests_completed", 0))
        elif condition_type == "level":
            current = int(getattr(self.party.leader, "level", 0)) if self.party else 0
        else:
            current = 0
        return min(current, target), target

    def conditions_met(self, conditions: list[dict[str, Any]] | dict[str, Any]) -> bool:
        if isinstance(conditions, dict):
            conditions = [conditions]
        return all(
            current >= target
            for current, target in (self.condition_progress(condition) for condition in conditions)
        )

    def quest_status(self, quest_id: str) -> str:
        quests = self.progression.setdefault("quests", {"active": [], "completed": [], "claimed": []})
        if quest_id in quests.get("claimed", []):
            return "claimed"
        quest = self.quest_catalog.get(quest_id, {})
        if quest_id in quests.get("active", []):
            return "claimable" if self.conditions_met(quest.get("conditions", {})) else "active"
        return "available"

    def claim_quest(self, quest_id: str) -> str | None:
        quest = self.quest_catalog.get(quest_id)
        if quest is None or self.quest_status(quest_id) != "claimable":
            return None

        rewards = quest.get("rewards", {})
        leader = self.party.leader if self.party else None
        if leader is not None:
            leader.gold += int(rewards.get("gold", 0))
            if rewards.get("xp"):
                leader.gain_xp(int(rewards["xp"]))
        for category in ("items", "weapons", "armors", "pets"):
            self.inventory.setdefault(category, {})
            for item_id, quantity in rewards.get(category, {}).items():
                self.inventory[category][item_id] = self.inventory[category].get(item_id, 0) + int(quantity)

        quests_state = self.progression["quests"]
        quests_state["active"].remove(quest_id)
        quests_state.setdefault("completed", []).append(quest_id)
        quests_state.setdefault("claimed", []).append(quest_id)
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
        )
        companion.reward_id = companion_id
        self.party.recruit(companion)
        title_state["reward_claimed"] = True
        return f"{companion.name} rejoint votre groupe."
