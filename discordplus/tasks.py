import logging

import discord.ext.tasks

logger = logging.getLogger("discordplus")


def safe_coro(func):
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
    return wrapped


def safe_loop(*args, **kwargs):
    def decorator(func):
        return discord.ext.tasks.loop(*args, **kwargs)(safe_coro(func))
    return decorator


def patch():
    discord.ext.tasks.safe_loop = safe_loop
