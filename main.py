from game_engine.games.asshole import AssholeGame
from game_engine.game_loop import GameLoop

if __name__ == "__main__":
    players = ["Alice", "Bob", "Charlie", "Larry"]
    game = AssholeGame(players)
    game_loop = GameLoop(game)
    game_loop.run()