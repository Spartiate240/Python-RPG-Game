"""
core/game.py

Point d'orchestration global : boucle de jeu, machine à états
(menu / exploration / combat / boutique), et lien entre les
autres modules (party, progression, sauvegarde).
main.py ne devrait faire quasiment que : Game().run()
"""

from __future__ import annotations
import json
from enum import Enum, auto
from pathlib import Path

from party.party import Party
from entities.player import Player
from core.menu import Menu
from core.fight import Fight

PROGRESSION_DIR = Path("progression")
GAME_SAVE_PATH = PROGRESSION_DIR / "Saved_progress.json"


class GameState(Enum):
    MAIN_MENU = auto()
    EXPLORATION = auto()
    STATUS = auto()
    FIGHT = auto()
    SHOP = auto()
    GAME_OVER = auto()
    QUIT = auto()


class Game:
    def __init__(self) -> None:
        self.state = GameState.MAIN_MENU
        self.party: Party | None = None
        self.location: str | None = None
        self.menu = Menu()
        self.inventory: dict[str, int] = {"items": {}, "weapons": {}, "armors": {}}

    # ---- Cycle de vie -----------------------------------------------
    def run(self) -> None:
        while self.state != GameState.QUIT:
            if self.state == GameState.MAIN_MENU:
                self._handle_main_menu()
            elif self.state == GameState.EXPLORATION:
                self._handle_exploration()
            elif self.state == GameState.FIGHT:
                self._handle_fight()
            elif self.state == GameState.STATUS:
                self._handle_status()
            elif self.state == GameState.SHOP:
                self._handle_shop()
            elif self.state == GameState.GAME_OVER:
                self._handle_game_over()

    # ---- Handlers d'état ---------------------------------------------
    def _handle_main_menu(self) -> None:
        choice = self.menu.show_main_menu()
        if choice == "new_game":
            self.party = self._new_party()
            self.location = None
            self.state = GameState.EXPLORATION
        elif choice == "load_game":
            self.party, self.state = self._load_progress()
        elif choice == "quit":
            self.state = GameState.QUIT

    def _handle_exploration(self) -> None:
        choice = self.menu.show_exploration_menu(self.party)
        if choice == "encounter":
            self.state = GameState.FIGHT
        elif choice == "shop":
            self.state = GameState.SHOP
        elif choice == "party_status":
            self.state = GameState.STATUS
        elif choice == "save":
            self._save_progress()
        elif choice == "quit":  # Sauvegarde aussi
            self._save_progress()
            self.state = GameState.QUIT

    def _handle_fight(self) -> None:
        from entities.enemy import Enemy
        enemies = [Enemy.from_id("goblin")]
        fight = Fight(self.party, enemies)
        result = fight.run()
        self.state = GameState.GAME_OVER if result == "defeat" else GameState.EXPLORATION

    def _handle_shop(self) -> None:
        self.menu.show_shop_menu(self.party)
        self.state = GameState.EXPLORATION

    def _handle_status(self) -> None:
        self.menu.show_party_status(self.party)
        if self.party and self.party.leader:
            self.menu._show_inventory(self.party, self.inventory)
        self.state = GameState.EXPLORATION

    def _handle_game_over(self) -> None:
        self.menu.show_game_over()
        self.state = GameState.QUIT

    # ---- Persistance --------------------------------------------------
    def _new_party(self) -> Party:
        hero = Player(name="Héros", max_hp=10, attack=1, defense=0, speed=1)
        return Party(members=[hero])

    def _save_progress(self) -> None:
        if self.party is None:
            return

        data = self.party.to_dict()
        game_state = {"state": self.state.name}
        if self.location is not None:
            game_state["location"] = self.location
        data["game_state"] = game_state
        data["inventory"] = self.inventory
        self._write_json(GAME_SAVE_PATH, data)

    def _load_progress(self) -> tuple[Party, GameState]:
        if not GAME_SAVE_PATH.exists():
            return self._new_party(), GameState.EXPLORATION

        data = self._read_json(GAME_SAVE_PATH)
        self.location = None

        game_state = data.get("game_state", {})
        if isinstance(game_state, dict):
            self.location = game_state.get("location")
            state_name = game_state.get("state", GameState.EXPLORATION.name)
        else:
            state_name = GameState.EXPLORATION.name

        self.inventory = data.get("inventory", {"items": {}, "weapons": {}, "armors": {}})
        try:
            state = GameState[state_name]
        except KeyError:
            state = GameState.EXPLORATION

        return Party.from_dict(data), state

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
