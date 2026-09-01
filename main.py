"""
main.py

Point d'entrée unique du jeu : l'interface pygame.
"""

from __future__ import annotations

from core.gui import PygameApp


def main() -> None:
    PygameApp().run()


if __name__ == "__main__":
    main()
