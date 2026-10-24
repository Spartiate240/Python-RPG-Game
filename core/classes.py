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
            member.class_node_id = getattr(member, "class_node_id", None) or self.default_node_id(member.class_id, member.tier)
            state = self.progression["classes"].setdefault(member.class_id, {})
            state["unlocked"] = True
            state.setdefault("mastery", 0)
            if "mastery_required" not in state or (int(member.tier) < 5 and int(state.get("mastery_required", 0)) == 0):
                state["mastery_required"] = self.next_mastery_required(member.class_id, member.tier)
            member.bind_classes(self.class_catalog, self.progression)

    def default_node_id(self, class_id: str, tier: int = 1) -> str:
        class_data = self.class_catalog.get(class_id, {})
        tiers = class_data.get("tiers", [])
        tier_data = next((entry for entry in tiers if int(entry.get("tier", 1)) == int(tier)), {})
        nodes = tier_data.get("nodes", [])
        if nodes:
            return str(nodes[0].get("id", f"{class_id}_t{tier}"))
        return f"{class_id}_t{tier}"

    def mastery_required(self, class_id: str, tier: int) -> int:
        class_data = self.class_catalog.get(class_id, {})
        tiers = class_data.get("tiers", [])
        tier_data = next((entry for entry in tiers if int(entry.get("tier", 1)) == int(tier)), {})
        return int(tier_data.get("mastery_required", max(100, int(tier) * 100)))

    def next_mastery_required(self, class_id: str, tier: int) -> int:
        next_tier = int(tier) + 1
        if not any(int(entry.get("tier", 1)) == next_tier for entry in self.class_catalog.get(class_id, {}).get("tiers", [])):
            return 0
        return self.mastery_required(class_id, next_tier)

    def state(self, class_id: str) -> dict[str, Any]:
        member = self.party.leader if self.party else None
        selected = member is not None and member.class_id == class_id
        progress = self.progression.setdefault("classes", {}).setdefault(class_id, {})
        return {
            "unlocked": selected,
            "tier": member.tier if selected else 1,
            "mastery": int(progress.get("mastery", 0)),
            "mastery_required": int(progress.get("mastery_required", self.next_mastery_required(class_id, member.tier if selected else 1))),
            "node_id": getattr(member, "class_node_id", None) if selected else self.default_node_id(class_id),
        }

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
        leader.class_node_id = self.default_node_id(class_id, 1)
        self.progression.setdefault("classes", {})[class_id] = {
            "mastery": 0,
            "mastery_required": self.next_mastery_required(class_id, 1),
            "unlocked": True,
        }
        self.progression["active_class"] = class_id
        leader.bind_classes(self.class_catalog, self.progression)
        return f"Classe choisie : {self.class_catalog[class_id].get('name', class_id)}."

    def choose_node(self, node_id: str) -> str:
        leader = self.party.leader if self.party else None
        if leader is None:
            return "Aucun personnage principal disponible."
        class_id, tier_data, node = self.node(node_id)
        if class_id is None or tier_data is None or node is None:
            return "Cette spécialisation n'existe pas."
        if leader.class_id != class_id:
            return "Cette spécialisation appartient à une autre voie."
        tier = int(tier_data.get("tier", 1))
        if tier > leader.tier:
            return "Ce tier n'est pas encore accessible."
        leader.class_node_id = node_id
        return f"Spécialisation choisie : {node.get('name', node_id)}."

    def node(self, node_id: str) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
        for class_id, class_data in self.class_catalog.items():
            for tier_data in class_data.get("tiers", []):
                for node in tier_data.get("nodes", []):
                    if str(node.get("id")) == node_id:
                        return class_id, tier_data, node
        return None, None, None

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
        leader = self.party.leader if self.party else None
        if leader is None or amount <= 0:
            return None
        class_id = leader.class_id
        state = self.progression.setdefault("classes", {}).setdefault(class_id, {})
        state["mastery"] = int(state.get("mastery", 0)) + int(amount)
        state["mastery_required"] = self.next_mastery_required(class_id, leader.tier)
        return f"Maîtrise de {self.class_catalog.get(class_id, {}).get('name', class_id)} : {state['mastery']}/{state['mastery_required']}"

    def requirements(self, class_id: str) -> list[str]:
        if self.state(class_id).get("unlocked") or self.class_catalog.get(class_id, {}).get("default"):
            return []
        return self._requirements(class_id)
