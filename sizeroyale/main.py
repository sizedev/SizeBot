import asyncio
import logging
from pathlib import Path

from digiformatter import logger as digilogger

from sizebot.lib import units
from sizebot.lib.loglevels import ROYALE
from sizeroyale.lib.classes.game import Game

# Logging stuff.
logging.basicConfig(level=logging.INFO)
dfhandler = digilogger.DigiFormatterHandler()
logger = logging.getLogger()
logger.handlers = []
logger.propagate = False
logger.addHandler(dfhandler)

asyncio.run(units.init())


def main():
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
