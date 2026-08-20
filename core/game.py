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
PARTY_SAVE_PATH = PROGRESSION_DIR / "party.json"
STATE_SAVE_PATH = PROGRESSION_DIR / "game_state.json"


class GameState(Enum):
    MAIN_MENU = auto()
    EXPLORATION = auto()
    FIGHT = auto()
    SHOP = auto()
    GAME_OVER = auto()
    QUIT = auto()


class Game:
    def __init__(self) -> None:
        self.state = GameState.MAIN_MENU
        self.party: Party | None = None
        self.menu = Menu()

    # ---- Cycle de vie -----------------------------------------------
    def run(self) -> None:
        while self.state != GameState.QUIT:
            if self.state == GameState.MAIN_MENU:
                self._handle_main_menu()
            elif self.state == GameState.EXPLORATION:
                self._handle_exploration()
            elif self.state == GameState.FIGHT:
                self._handle_fight()
            elif self.state == GameState.SHOP:
                self._handle_shop()
            elif self.state == GameState.GAME_OVER:
                self._handle_game_over()

    # ---- Handlers d'état ---------------------------------------------
    def _handle_main_menu(self) -> None:
        choice = self.menu.show_main_menu()
        if choice == "new_game":
            self.party = self._new_party()
            self.state = GameState.EXPLORATION
        elif choice == "load_game":
            self.party = self._load_party()
            self.state = self._load_game_state()
        elif choice == "quit":
            self.state = GameState.QUIT

    def _handle_exploration(self) -> None:
        choice = self.menu.show_exploration_menu(self.party)
        if choice == "encounter":
            self.state = GameState.FIGHT
        elif choice == "shop":
            self.state = GameState.SHOP
        elif choice == "save":
            self._save_game()
        elif choice == "quit":
            self._save_game()
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

    def _handle_game_over(self) -> None:
        self.menu.show_game_over()
        self.state = GameState.QUIT

    # ---- Persistance --------------------------------------------------
    def _new_party(self) -> Party:
        hero = Player(name="Héros", max_hp=100, attack=15, defense=8, speed=10)
        return Party(members=[hero])

    def _save_game(self) -> None:
        self._save_party()
        self._save_game_state()

    def _save_party(self) -> None:
        self._write_json(PARTY_SAVE_PATH, self.party.to_dict())

    def _save_game_state(self) -> None:
        self._write_json(STATE_SAVE_PATH, {"state": self.state.name})

    def _load_party(self) -> Party:
        if not PARTY_SAVE_PATH.exists():
            return self._new_party()
        data = self._read_json(PARTY_SAVE_PATH)
        return Party.from_dict(data)

    def _load_game_state(self) -> GameState:
        if not STATE_SAVE_PATH.exists():
            return GameState.EXPLORATION
        data = self._read_json(STATE_SAVE_PATH)
        try:
            return GameState[data.get("state", GameState.EXPLORATION.name)]
        except KeyError:
            return GameState.EXPLORATION

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))
