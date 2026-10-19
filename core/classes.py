"""Regles d'apprentissage des classes, independantes de pygame."""

from __future__ import annotations

from typing import Any

from party.party import Party


class ClassService:
    """Gère la classe choisie et les tiers des membres du groupe."""

    def __init__(self, class_catalog: dict[str, dict[str, Any]], quest_catalog: dict[str, dict[str, Any]]) -> None:
        self.class_catalog = class_catalog
        self.quest_catalog = quest_catalog
        self.party: Party | None = None
        self.progression: dict[str, Any] = {}

    def bind(self, party: Party | None, progression: dict[str, Any]) -> None:
        self.party = party
        self.progression = progression
        self.progression.setdefault("classes", {})
        for member in self.party.members if self.party else []:
            if member.class_id not in self.class_catalog:
                member.class_id = "warrior"
                member.tier = 1
            member.bind_classes(self.class_catalog, self.progression)

    def state(self, class_id: str) -> dict[str, Any]:
        member = self.party.leader if self.party else None
        selected = member is not None and member.class_id == class_id
        return {"unlocked": selected, "tier": member.tier if selected else 1}

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
        return class_id in self.class_catalog

    def choose(self, class_id: str) -> str:
        if class_id not in self.class_catalog:
            return "Cette classe n'existe pas."
        if self.party is None or self.party.leader is None:
            return "Aucun personnage principal disponible."
        leader = self.party.leader
        leader.set_class(class_id, 1, preserve_hp_ratio=False)
        leader.bind_classes(self.class_catalog, self.progression)
        return f"Classe choisie : {self.class_catalog[class_id].get('name', class_id)}."

    def learn(self, class_id: str) -> str:
        return self.choose(class_id)

    def _condition_requirements(self, requirements: dict[str, Any]) -> list[str]:
        if not requirements:
            return []
        class_id = self.progression.get("active_class")
        if class_id is None:
            return []
        return self._requirements(class_id, requirements)

    def gain_mastery(self, amount: int = 0) -> str | None:
        return None

    def requirements(self, class_id: str) -> list[str]:
        if self.state(class_id).get("unlocked") or self.class_catalog.get(class_id, {}).get("default"):
            return []
        return self._requirements(class_id)
