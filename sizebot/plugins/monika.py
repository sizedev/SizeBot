import random

import importlib.resources as pkg_resources
import logging

import sizebot.data

logger = logging.getLogger("sizebot")
monikalines = pkg_resources.read_text(sizebot.data, "monikalines.txt").splitlines()


async def on_message(m):
    """Monika easter eggs."""
    if m.author.bot:
        return
    if "monika" not in m.content.lower():
        return
    logger.warn("Monika detected.")
    if random.randrange(6) == 1:
        logger.warn("Monika triggered.")
        line = random.choice(monikalines)
        await m.channel.send(line, delete_after = 7)
