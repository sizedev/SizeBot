from discord.ext import commands

from sizebot.lib.constants import emojis
from sizebot.lib.menu import Menu

numberemojis = [
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "0️⃣"
]


class TestCog(commands.Cog):
    """Test commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def test(self, ctx):
        reactionmenu, answer = await Menu.display(ctx, numberemojis, cancel_emoji = emojis.cancel,
                                                  initial_message = "This is a test menu!", delete_after = False)
        if answer in numberemojis:
            await reactionmenu.message.edit(content = reactionmenu.message.content + f"\nYou pressed {answer}. Good job!")


async def setup(bot):
    await bot.add_cog(TestCog(bot))
