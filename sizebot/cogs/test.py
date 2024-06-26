from discord.ext import commands

from sizebot.lib.statproxy import StatProxy
from sizebot.lib.types import BotContext


class TestCog(commands.Cog):
    """Test commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    async def test(self, ctx: BotContext, stat: StatProxy | str):
        if isinstance(stat, StatProxy):
            await ctx.send(f"You input **\"{stat.name}\"**\nIt's a **{'tag' if stat.tag else 'stat'}.**")
        else:
            await ctx.send(f"You input **\"{stat}\"**. That's not a stat or a tag.")


async def setup(bot: commands.Bot):
    await bot.add_cog(TestCog(bot))
