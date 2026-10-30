import rogueultralite.game as game

def main() -> None:
    the_game = game.Game()
    the_game.run_game()

    print(the_game.win)