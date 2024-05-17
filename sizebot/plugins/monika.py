import random

import importlib.resources as pkg_resources
import logging

import discord

import sizebot.data

logger = logging.getLogger("sizebot")
monikalines = pkg_resources.read_text(sizebot.data, "monikalines.txt").splitlines()


async def on_message(m: discord.Message):
    """Monika easter eggs."""
    if m.author.bot:
        return
    if "monika" not in m.content.lower():
        return
    logger.debug("Monika detected.")
    if random.randrange(6) == 1:
        logger.info("Monika triggered.")
        line = random.choice(monikalines)
        await m.channel.send(line, delete_after = 7)
