from typing import TypedDict, cast

import discord.utils
from discord import Guild, Member
from discord.ext import commands

class GuildContext(commands.Context[commands.Bot]):
    @discord.utils.cached_property
    def guild(self) -> Guild:
        """:class:`.Guild`: Returns the guild associated with this context's command. None if not available."""
        return cast(Guild, self.message.guild)

    @discord.utils.cached_property
    def author(self) -> Member:
        """:class:`.Guild`: Returns the guild associated with this context's command. None if not available."""
        return cast(Member, self.message.author)

BotContext = commands.Context[commands.Bot]

class EmbedToSend(TypedDict):
    embed: str


class StrToSend(TypedDict):
    content: str


class EmbedField(TypedDict):
    name: str
    value: str
    inline: bool
