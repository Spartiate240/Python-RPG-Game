"""
core/fight.py

Boucle de combat au tour par tour. Ne connaît RIEN des détails
d'implémentation des personnages : il manipule des Combatant
via choose_action() et Action, ce qui fait que Player, Companion
et Enemy sont interchangeables ici.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from entities.combatant import Combatant, Action

if TYPE_CHECKING:
    from party.party import Party
    from entities.enemy import Enemy


class Fight:
    def __init__(self, party: "Party", enemies: list["Enemy"]) -> None:
        self.party = party
        self.enemies = enemies

    def run(self) -> str:
        """Retourne 'victory', 'defeat' ou 'flee'."""
        print("\n=== UN COMBAT COMMENCE ===")

        while True:
            turn_order = self._turn_order()

            for combatant in turn_order:
                if not combatant.is_alive():
                    continue
                if self._is_battle_over():
                    break

                allies_side, enemies_side = self._sides_for(combatant)
                action = combatant.choose_action(allies_side, enemies_side)
                self._resolve(combatant, action)

            outcome = self._check_outcome()
            if outcome:
                return outcome

    # ---- Ordre et camps -----------------------------------------------
    def _turn_order(self) -> list[Combatant]:
        combatants = [*self.party.active_members(), *self.enemies]
        return sorted(combatants, key=lambda c: c.speed, reverse=True)

    def _sides_for(self, combatant: Combatant) -> tuple[list[Combatant], list[Combatant]]:
        if combatant in self.enemies:
            return self.enemies, list(self.party.active_members())
        return list(self.party.active_members()), self.enemies

    # ---- Résolution d'une action ---------------------------------------
    def _resolve(self, actor: Combatant, action: Action) -> None:
        if action.kind == "attack" and action.target:
            damage = max(1, actor.attack - action.target.defense)
            dealt = action.target.take_damage(damage)
            print(f"{actor.name} attaque {action.target.name} pour {dealt} dégâts.")

        elif action.kind == "skill" and "skill" in action.payload:
            skill = action.payload["skill"]
            skill.execute(actor, action.target)

        elif action.kind == "item" and "item" in action.payload:
            item = action.payload["item"]
            item.use(actor)

        elif action.kind == "defend":
            print(f"{actor.name} se met en garde.")

    # ---- Fin de combat --------------------------------------------------
    def _is_battle_over(self) -> bool:
        return self._check_outcome() is not None

    def _check_outcome(self) -> str | None:
        if not any(a.is_alive() for a in self.party.active_members()):
            return "defeat"
        if not any(e.is_alive() for e in self.enemies):
            self._grant_rewards()
            return "victory"
        return None

    def _grant_rewards(self) -> None:
        total_xp = sum(e.xp_reward for e in self.enemies)
        total_gold = sum(e.gold_reward for e in self.enemies)
        for member in self.party.active_members():
            member.gain_xp(total_xp)
        if self.party.leader:
            self.party.leader.gold += total_gold
        print(f"Victoire ! +{total_xp} XP, +{total_gold} or.")
