import discord
from discord.ext import commands


async def setup(bot: commands.Bot):
    @bot.listen
    def on_command(ctx: commands.Context[commands.Bot]) -> bool:
        member = ctx.author
        isMember = isinstance(member, discord.Member)
        if not isMember:
            return True
        isGuildBanned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
        return not isGuildBanned
