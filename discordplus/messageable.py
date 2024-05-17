from typing import AsyncIterator, Any

from discord.abc import Messageable
import discord

old_history = Messageable.history


# TODO: CamelCase
def wrapSnowflake(name: str, kwargs: dict[str, Any]):
    if name not in kwargs:
        return
    value = kwargs[name]
    if isinstance(value, int):
        kwargs[name] = discord.Snowflake(value)


def history(self: Messageable, **kwargs) -> AsyncIterator[discord.Message]:
    wrapSnowflake("before", kwargs)
    wrapSnowflake("after", kwargs)
    wrapSnowflake("around", kwargs)

    return old_history(self, **kwargs)


def patch():
    Messageable.history = history
