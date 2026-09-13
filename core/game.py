"""
core/game.py

Gestion de la progression du jeu et de l'état de sauvegarde.
Le flux de jeu est piloté par l'interface pygame et les fichiers
de sauvegarde du projet.
"""

from __future__ import annotations
import json
from enum import Enum, auto
from pathlib import Path

from party.party import Party
from entities.player import Player

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
        self.inventory: dict[str, dict[str, int]] = {"items": {}, "weapons": {}, "armors": {}, "pets": {}}
        self.merchant_stock: dict = {}
        self.progression: dict = {
            "stats": {"victories": 0, "gold_earned": 0, "quests_completed": 0},
            "quests": {"active": [], "completed": [], "claimed": []},
            "titles": {},
        }

    # ---- Persistance --------------------------------------------------
    def _new_party(self) -> Party:
        hero = Player(name="Héros", max_hp=10, attack=1, defense=0, speed=1)
        return Party(members=[hero])

    def new_game(self) -> None:
        """Initialise un nouvel état de jeu prêt à être présenté par l'UI."""
        self.party = self._new_party()
        self.state = GameState.EXPLORATION
        self.location = "village"
        self.inventory = {"items": {}, "weapons": {}, "armors": {}, "pets": {}}
        self.merchant_stock = {}
        self.progression = {
            "stats": {"victories": 0, "gold_earned": 0, "quests_completed": 0},
            "quests": {"active": [], "completed": [], "claimed": []},
            "titles": {},
        }

    def load_game(self) -> GameState:
        """Charge la sauvegarde et retourne l'état persistant de la partie."""
        self.party, self.state = self._load_progress()
        return self.state

    def save_game(
        self,
        party: Party,
        location: str | None,
        inventory: dict[str, dict[str, int]],
        progression: dict,
        state: GameState,
        merchant_stock: dict | None = None,
    ) -> None:
        """Enregistre l'état fourni par le coordinateur de l'application."""
        self.party = party
        self.location = location
        self.inventory = inventory
        self.progression = progression
        self.merchant_stock = merchant_stock or {}
        self.state = state
        self._save_progress()

    def _save_progress(self) -> None:
        if self.party is None:
            return

        self.inventory.setdefault("pets", {})
        data = self.party.to_dict()
        game_state = {"state": self.state.name}
        if self.location is not None:
            game_state["location"] = self.location
        data["game_state"] = game_state
        data["inventory"] = self.inventory
        data["progression"] = self.progression
        data["merchant_stock"] = self.merchant_stock
        self._write_json(GAME_SAVE_PATH, data)

    def _load_progress(self) -> tuple[Party, GameState]:
        if not GAME_SAVE_PATH.exists():
            return self._new_party(), GameState.EXPLORATION

        try:
            data = self._read_json(GAME_SAVE_PATH)
        except (json.JSONDecodeError, OSError):
            return self._new_party(), GameState.EXPLORATION
        self.location = None

        game_state = data.get("game_state", {})
        if isinstance(game_state, dict):
            self.location = game_state.get("location")
            state_name = game_state.get("state", GameState.EXPLORATION.name)
        else:
            state_name = GameState.EXPLORATION.name

        self.inventory = data.get("inventory", {"items": {}, "weapons": {}, "armors": {}, "pets": {}})
        self.inventory.setdefault("pets", {})
        self.progression = data.get("progression", self.progression)
        self.merchant_stock = data.get("merchant_stock", {})
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
