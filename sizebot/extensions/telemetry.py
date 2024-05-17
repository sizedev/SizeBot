import discord
from discord.ext import commands

from sizebot.lib.types import BotContext


async def setup(bot: commands.Bot):
    @bot.listen
    def on_command(ctx: BotContext) -> bool:
        member = ctx.author
        isMember = isinstance(member, discord.Member)
        if not isMember:
            return True
        isGuildBanned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
        return not isGuildBanned
