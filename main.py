"""
main.py
 
Point d'entrée du jeu. Ne devrait quasiment rien faire d'autre
que démarrer la boucle principale gérée par core/game.py.
"""
 
from core.game import Game
 
 
def main() -> None:
    game = Game()
    game.run()
 
 
if __name__ == "__main__":
    main()
 
