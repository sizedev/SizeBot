import asyncio
import logging
from pathlib import Path

from sizebot.lib import units
from sizebot.lib.loglevels import ROYALE
from sizeroyale.lib.classes.game import Game

logger = logging.get("sizebot")

asyncio.run(units.init())


def main():
    test()


def test():
    logger.info("Welcome to the poopview!")
    game = Game(Path(__file__).parent.parent / "royale-spec.txt")
    logger.info(game)
    logger.log(ROYALE, f"seed = {game.seed}")
    print(game.royale.current_players)
    game.royale.stats_screen.show()

    while game.game_over is None:
        game.next()

    logger.info("Your poop has been viewed.")


if __name__ == "__main__":
    main()
