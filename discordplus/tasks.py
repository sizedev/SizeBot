from typing import Any
from collections.abc import Callable

import logging

import discord.ext.tasks

logger = logging.getLogger("discordplus")


def safe_coro(func: Callable) -> Callable:
    async def wrapped(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
    return wrapped


def safe_loop(*args, **kwargs) -> Callable:
    def decorator(func: Callable) -> discord.ext.tasks.Loop:
        return discord.ext.tasks.loop(*args, **kwargs)(safe_coro(func))
    return decorator


def patch():
    discord.ext.tasks.safe_loop = safe_loop
