"""
entities/ally.py

Ally = tout ce qui combat du côté du joueur (Player, Companion).
C'est ici que vivent : niveau/xp, équipement, compétences.
Player et Companion héritent de cette classe et ne font que
spécialiser le "cerveau" (choose_action) et quelques attributs.
"""

from __future__ import annotations
import re
from typing import TYPE_CHECKING, Any

from entities.combatant import Combatant, Action

if TYPE_CHECKING:
    from skills.skills import Skill


class Ally(Combatant):
    def __init__(
        self,
        name: str,
        max_hp: int,
        attack: int,
        defense: int,
        speed: int,
        level: int = 1,
        xp: int = 0,
        inventory: list[Any] | None = None,
        class_id: str = "warrior",
        tier: int = 1,
    ) -> None:
        super().__init__(name, max_hp, attack, defense, speed)
        self._fallback_stats = {
            "max_hp": int(max_hp),
            "attack": int(attack),
            "defense": int(defense),
            "speed": int(speed),
        }
        self.level = level
        self.xp = xp
        self.class_id = class_id
        self.tier = max(1, int(tier))
        self.inventory: list[Any] = inventory or []

        self.weapon_primary: Any | None = None
        self.weapon_secondary: Any | None = None
        self.helmet: Any | None = None
        self.chest: Any | None = None
        self.legs: Any | None = None
        self.boots: Any | None = None
        self.arms: Any | None = None
        self.pet: Any | None = None
        self.skills: list["Skill"] = []
        self.class_catalog: dict[str, dict[str, Any]] = {}
        self.class_progression: dict[str, Any] = {}

    @property
    def class_data(self) -> dict[str, Any]:
        return self.class_catalog.get(self.class_id, {})

    @property
    def tier_data(self) -> dict[str, Any]:
        tiers = self.class_data.get("tiers", [])
        index = min(max(self.tier - 1, 0), len(tiers) - 1)
        return tiers[index] if tiers else {}

    @property
    def class_name(self) -> str:
        return str(self.class_data.get("name", self.class_id))

    @property
    def tier_name(self) -> str:
        return str(self.tier_data.get("name", f"Tier {self.tier}"))

    def _derived_stat(self, stat: str) -> int:
        class_data = self.class_data
        if not class_data:
            return int(self._fallback_stats.get(stat, 0))
        base = int(class_data.get("base_stats", {}).get(stat, self._fallback_stats.get(stat, 0)))
        growth = int(class_data.get("growth", {}).get(stat, 0))
        multiplier = float(self.tier_data.get("growth_multiplier", 1.0))
        bonus = int(self.tier_data.get("stat_bonus", {}).get(stat, 0))
        return int(round(base + growth * (self.level - 1) * multiplier + bonus))

    @property
    def attack(self) -> int:
        return self._derived_stat("attack")

    @attack.setter
    def attack(self, value: int) -> None:
        if not hasattr(self, "_fallback_stats"):
            self._fallback_stats = {}
        self._fallback_stats["attack"] = int(value)

    @property
    def defense(self) -> int:
        return self._derived_stat("defense")

    @defense.setter
    def defense(self, value: int) -> None:
        if not hasattr(self, "_fallback_stats"):
            self._fallback_stats = {}
        self._fallback_stats["defense"] = int(value)

    @property
    def speed(self) -> int:
        return self._derived_stat("speed")

    @speed.setter
    def speed(self, value: int) -> None:
        if not hasattr(self, "_fallback_stats"):
            self._fallback_stats = {}
        self._fallback_stats["speed"] = int(value)

    # ---- Équipement ------------------------------------------------
    def equip_weapon(self, weapon: Any) -> None:
        self.weapon_primary = weapon

    def equip_weapon_secondary(self, weapon: Any | None) -> None:
        self.weapon_secondary = weapon

    def equip_helmet(self, helmet: Any) -> None:
        self.helmet = helmet

    def equip_chest(self, chest: Any) -> None:
        self.chest = chest

    def equip_legs(self, legs: Any) -> None:
        self.legs = legs

    def equip_boots(self, boots: Any) -> None:
        self.boots = boots

    def equip_arms(self, arms: Any) -> None:
        self.arms = arms

    def equip_pet(self, pet: Any | None) -> None:
        self.pet = pet

    def equip_armor(self, armor: Any) -> None:
        self.equip_chest(armor)

    @property
    def armor(self) -> Any | None:
        return self.chest

    @armor.setter
    def armor(self, value: Any | None) -> None:
        self.chest = value

    @property
    def total_attack(self) -> int:
        bonuses = (
            _item_value(self.weapon_primary, ("attack_bonus", "damage")),
            _item_value(self.weapon_secondary, ("attack_bonus", "damage")),
            _pet_attack_bonus(self.pet),
        )
        return self.attack + sum(bonuses) + self.class_stat_bonus("damage")

    @property
    def total_defense(self) -> int:
        bonuses = (
            _item_value(self.helmet, ("defense_bonus", "defense")),
            _item_value(self.chest, ("defense_bonus", "defense")),
            _item_value(self.legs, ("defense_bonus", "defense")),
            _item_value(self.boots, ("defense_bonus", "defense")),
            _item_value(self.arms, ("defense_bonus", "defense")),
        )
        return self.defense + sum(bonuses) + self.class_stat_bonus("defense")

    @property
    def total_speed(self) -> int:
        return self.speed + self.class_stat_bonus("speed")

    @property
    def max_hp(self) -> int:
        equipment_health = sum(
            _item_value(getattr(self, slot, None), ("health", "max_health"))
            for slot in ("helmet", "chest", "legs", "boots", "arms")
        )
        return self._derived_stat("max_hp") + equipment_health

    @max_hp.setter
    def max_hp(self, value: int) -> None:
        self._base_max_hp = int(value)
        if hasattr(self, "_fallback_stats"):
            self._fallback_stats["max_hp"] = int(value)

    def bind_classes(self, class_catalog: dict[str, dict[str, Any]], progression: dict[str, Any]) -> None:
        self.class_catalog = class_catalog
        self.class_progression = progression

    def refresh_stats(self, preserve_hp_ratio: bool = True) -> None:
        saved_ratio = getattr(self, "_saved_hp_ratio", None)
        previous_max_hp = max(1, int(getattr(self, "_last_max_hp", self.max_hp)))
        ratio = saved_ratio if saved_ratio is not None else max(0.0, min(1.0, self.hp / previous_max_hp))
        self._last_max_hp = self.max_hp
        if saved_ratio is not None:
            del self._saved_hp_ratio
        self.hp = int(round(self.max_hp * ratio)) if preserve_hp_ratio else self.max_hp

    def set_class(self, class_id: str, tier: int = 1, preserve_hp_ratio: bool = True) -> None:
        previous_max_hp = max(1, self.max_hp)
        ratio = max(0.0, min(1.0, self.hp / previous_max_hp))
        self.class_id = class_id
        self.tier = max(1, int(tier))
        self.hp = int(round(self.max_hp * ratio)) if preserve_hp_ratio else self.max_hp

    @property
    def base_max_hp(self) -> int:
        return self._derived_stat("max_hp")

    def _active_class_data(self) -> tuple[dict[str, Any], dict[str, Any]] | None:
        class_id = getattr(self, "class_progression", {}).get("active_class")
        class_data = getattr(self, "class_catalog", {}).get(class_id or "")
        state = getattr(self, "class_progression", {}).get("classes", {}).get(class_id or "", {})
        if not class_data or not state.get("unlocked"):
            return None
        return class_data, state

    def _class_effects(self) -> list[dict[str, Any]]:
        active = self._active_class_data()
        if active is None:
            return []
        class_data, state = active
        tier_index = max(0, min(int(state.get("tier", 1)) - 1, len(class_data.get("tiers", [])) - 1))
        return list(class_data.get("tiers", [])[tier_index].get("effects", []))

    def _effect_requirements_met(self, requirements: dict[str, Any]) -> bool:
        if not requirements:
            return True
        armor_type = requirements.get("armor_type")
        weapon_type = requirements.get("weapon_type")
        if armor_type:
            return any(_item_type(getattr(self, slot, None)) == armor_type for slot in ("helmet", "chest", "legs", "boots", "arms"))
        if weapon_type:
            return any(_item_type(getattr(self, slot, None)) == weapon_type for slot in ("weapon_primary", "weapon_secondary"))
        return True

    def class_stat_bonus(self, stat: str) -> int:
        total = 0
        for effect in self._class_effects():
            if self._effect_requirements_met(effect.get("requires", {})):
                total += int(effect.get("stats", {}).get(stat, 0))
        return total

    def class_passives(self, trigger: str) -> list[dict[str, Any]]:
        return [
            effect["passive"]
            for effect in self._class_effects()
            if effect.get("passive") and effect["passive"].get("trigger") == trigger
            and self._effect_requirements_met(effect.get("requires", {}))
        ]

    # ---- Compétences -------------------------------------------------
    def learn_skill(self, skill: "Skill") -> None:
        if skill not in self.skills:
            self.skills.append(skill)

    # ---- Progression ---------------------------------------------
    def gain_xp(self, amount: int) -> None:
        from progression.level_manager import LevelManager

        LevelManager().add_xp(self, amount)

    # choose_action() reste abstrait : Player (input utilisateur)
    # et Companion (IA) l'implémentent chacun à leur façon.


def _item_value(item: Any | None, keys: tuple[str, ...]) -> int:
    if item is None:
        return 0
    if isinstance(item, dict):
        for key in keys:
            value = item.get(key)
            if isinstance(value, (int, float)):
                return int(value)
        return 0
    for key in keys:
        value = getattr(item, key, None)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def _pet_attack_bonus(pet: Any | None) -> int:
    """Extracts the attack bonus from a pet's data-driven effect."""
    effect = _value(pet, "effect")
    explicit_bonus = _value(pet, "attack_bonus")
    if isinstance(explicit_bonus, (int, float)):
        return int(explicit_bonus)
    if not isinstance(effect, str):
        return 0
    match = re.search(r"attack\s+increased\s+by\s+(\d+)", effect, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def _value(item: Any | None, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _item_type(item: Any | None) -> str | None:
    value = _value(item, "type")
    return str(value) if value is not None else None
