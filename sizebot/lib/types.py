from typing import TypedDict

from discord.ext import commands

BotContext = commands.Context[commands.Bot]


class EmbedToSend(TypedDict):
    embed: str


class StrToSend(TypedDict):
    content: str


class EmbedField(TypedDict):
    name: str
    value: str
    inline: bool
