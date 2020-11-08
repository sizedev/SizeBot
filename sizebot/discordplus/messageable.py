from discord.abc import Messageable
import discord

old_history = Messageable.history


def wrapSnowflake(name, kwargs):
    if name not in kwargs:
        return
    value = kwargs[name]
    if isinstance(value, int):
        kwargs[name] = discord.Snowflake(value)


def history(self, **kwargs):
    wrapSnowflake("before", kwargs)
    wrapSnowflake("after", kwargs)
    wrapSnowflake("around", kwargs)

    return old_history(self, **kwargs)


def patch():
    Messageable.history = history
