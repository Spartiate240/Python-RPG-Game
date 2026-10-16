"""Gestion des sauvegardes nommees et des emplacements de partie."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from progression import crypto


ROOT_DIR = Path(__file__).resolve().parents[1]
PROGRESSION_DIR = ROOT_DIR / "progression"
SAVE_DIR = PROGRESSION_DIR / "saves"
LEGACY_SAVE_PATH = PROGRESSION_DIR / "Saved_progress.json"


@dataclass(frozen=True)
class SaveSlot:
    """Emplacement de sauvegarde affichable dans le menu."""

    label: str
    path: Path
    legacy: bool = False


class SaveManager:
    """Liste et prepare les fichiers de sauvegarde sans les ecraser."""

    def list_slots(self) -> list[SaveSlot]:
        slots: list[SaveSlot] = []
        if LEGACY_SAVE_PATH.exists():
            slots.append(SaveSlot("Sauvegarde principale", LEGACY_SAVE_PATH, legacy=True))
        if SAVE_DIR.exists():
            for path in sorted(SAVE_DIR.glob("*.json")):
                label = self._display_name(path)
                try:
                    data = crypto.read_save(path)
                    label = str(data.get("profile", {}).get("name", label))
                except (OSError, ValueError, crypto.SaveError):
                    label = f"{label} (illisible)"
                slots.append(SaveSlot(label, path))
        return slots

    def create_path(self, name: str) -> Path:
        """Retourne un nouveau chemin unique pour le nom saisi."""
        slug = self._slugify(name)
        candidate = SAVE_DIR / f"{slug}.json"
        index = 2
        while candidate.exists():
            candidate = SAVE_DIR / f"{slug}_{index}.json"
            index += 1
        return candidate

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).strip("_")
        return slug[:40] or "partie"

    @staticmethod
    def _display_name(path: Path) -> str:
        return path.stem.replace("_", " ").replace("-", " ").title()
