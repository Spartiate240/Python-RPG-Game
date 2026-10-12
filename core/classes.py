"""Regles d'apprentissage des classes, independantes de pygame."""

from __future__ import annotations

from typing import Any

from party.party import Party


class ClassService:
    """Expose l'etat et les prerequis des classes du catalogue."""

    def __init__(self, class_catalog: dict[str, dict[str, Any]], quest_catalog: dict[str, dict[str, Any]]) -> None:
        self.class_catalog = class_catalog
        self.quest_catalog = quest_catalog
        self.party: Party | None = None
        self.progression: dict[str, Any] = {}

    def bind(self, party: Party | None, progression: dict[str, Any]) -> None:
        self.party = party
        self.progression = progression
        states = self.progression.setdefault("classes", {})
        self.progression.setdefault("active_class", "adventurer")
        for class_id, class_data in self.class_catalog.items():
            state = states.setdefault(class_id, {})
            state.setdefault("unlocked", bool(class_data.get("default", False)))
            state.setdefault("mastery", 0)
            state.setdefault("tier", 1)
            if class_data.get("default") and not self.progression.get("active_class"):
                self.progression["active_class"] = class_id
            for member in self.party.members if self.party else []:
                member.bind_classes(self.class_catalog, self.progression)

    def state(self, class_id: str) -> dict[str, Any]:
        return self.progression.setdefault("classes", {}).setdefault(
            class_id,
            {"unlocked": False, "mastery": 0, "tier": 1},
        )

    def _requirements(self, class_id: str, unlock: dict[str, Any] | None = None) -> list[str]:
        class_data = self.class_catalog.get(class_id, {})
        unlock = class_data.get("unlock") if unlock is None else unlock
        unlock = unlock or {}
        stats = self.progression.setdefault("stats", {})
        leader = self.party.leader if self.party else None
        requirements: list[str] = []

        level = int(unlock.get("level", 0))
        if level and (leader is None or int(leader.level) < level):
            requirements.append(f"Niveau {level}")

        quests_completed = int(unlock.get("quests_completed", 0))
        current_quests = int(stats.get("quests_completed", 0))
        if quests_completed and current_quests < quests_completed:
            requirements.append(f"{quests_completed} quêtes terminées ({current_quests}/{quests_completed})")

        wins_with = unlock.get("wins_with") or {}
        quantity = int(wins_with.get("quantity", 0))
        if quantity:
            equipment = wins_with.get("armor_type") or wins_with.get("weapon_type")
            key = f"wins_with_{equipment}"
            current_wins = int(stats.get(key, 0))
            if current_wins < quantity:
                requirements.append(f"{quantity} victoires avec {equipment} ({current_wins}/{quantity})")

        trainer_quest = unlock.get("trainer_quest")
        if trainer_quest and trainer_quest in self.quest_catalog:
            completed = self.progression.setdefault("quests", {}).get("completed", [])
            if trainer_quest not in completed:
                requirements.append(f"Quête d'apprentissage : {trainer_quest}")
        return requirements

    def is_available(self, class_id: str) -> bool:
        state = self.state(class_id)
        class_data = self.class_catalog.get(class_id, {})
        return bool(state.get("unlocked")) or bool(class_data.get("default")) or not self._requirements(class_id)

    def learn(self, class_id: str) -> str:
        class_data = self.class_catalog.get(class_id)
        if class_data is None:
            return "Cette classe n'existe pas."
        state = self.state(class_id)
        if state.get("unlocked"):
            return f"Classe déjà apprise : {class_data.get('name', class_id)}."
        requirements = self._requirements(class_id)
        if requirements:
            return "Prérequis manquants : " + ", ".join(requirements) + "."
        state["unlocked"] = True
        self.progression["active_class"] = class_id
        for member in self.party.members if self.party else []:
            member.bind_classes(self.class_catalog, self.progression)
        return f"Classe apprise : {class_data.get('name', class_id)}."

    def _condition_requirements(self, requirements: dict[str, Any]) -> list[str]:
        if not requirements:
            return []
        class_id = self.progression.get("active_class")
        if class_id is None:
            return []
        return self._requirements(class_id, requirements)

    def gain_mastery(self, amount: int = 0) -> str | None:
        class_id = self.progression.get("active_class")
        if not class_id or not self.state(class_id).get("unlocked"):
            return None
        state = self.state(class_id)
        state["mastery"] = int(state.get("mastery", 0)) + max(0, int(amount))
        class_data = self.class_catalog.get(class_id, {})
        tiers = class_data.get("tiers", [])
        message = None
        while int(state.get("tier", 1)) < len(tiers):
            next_tier = tiers[int(state["tier"])]
            if int(state["mastery"]) < int(next_tier.get("mastery_required", 0)):
                break
            if self._condition_requirements(next_tier.get("requirements") or {}):
                break
            state["tier"] = int(state["tier"]) + 1
            message = f"Nouveau palier : {next_tier.get('name', class_id)}."
        return message

    def requirements(self, class_id: str) -> list[str]:
        if self.state(class_id).get("unlocked") or self.class_catalog.get(class_id, {}).get("default"):
            return []
        return self._requirements(class_id)
