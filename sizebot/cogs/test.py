from discord.ext import commands
from sizebot.discordplus import commandsplus

from sizebot.lib import menu
from sizebot.lib.constants import emojis

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

    @commandsplus.command(
        hidden = True
    )
    @commands.is_owner()
    async def test(self, ctx):
        reactionmenu = await menu.Menu(ctx, "This is a test menu!", numberemojis, cancel_emoji = emojis.cancel)
        menu_message = reactionmenu.message
        answer = await reactionmenu.run()
        if answer in numberemojis:
            menu_message.edit(content = menu_message.content + f"\nYou pressed {answer}. Good job!")


def setup(bot):
    bot.add_cog(TestCog(bot))
