from typing import Union
from discord.ext import commands

from sizebot.lib.statproxy import StatProxy


class TestCog(commands.Cog):
    """Test commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    async def test(self, ctx: commands.Context, stat: Union[StatProxy, str]):
        if isinstance(stat, StatProxy):
            await ctx.send(f"You input **\"{stat.name}\"**\nIt's a **{'tag' if stat.tag else 'stat'}.**")
        else:
            await ctx.send(f"You input **\"{stat}\"**. That's not a stat or a tag.")


async def setup(bot):
    await bot.add_cog(TestCog(bot))
