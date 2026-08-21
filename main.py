"""
main.py

Point d'entrée du jeu. Lance la version pygame par défaut,
ou la version terminal avec --text.
"""

from __future__ import annotations

import argparse

from core.game import Game


def main() -> None:
    parser = argparse.ArgumentParser(description="Python RPG Game")
    parser.add_argument("--text", action="store_true", help="Lancer la version terminal")
    args = parser.parse_args()

    if args.text:
        Game().run()
        return

    from core.gui import PygameApp

    PygameApp().run()


if __name__ == "__main__":
    main()
