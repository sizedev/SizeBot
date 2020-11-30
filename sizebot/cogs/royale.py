from sizeroyale import Game
from discord.ext import commands

current_games = {}


class RoyaleCog(commands.Cog):
    """Play a game of Size Royale!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    @commands.has_any_role("Royale DM", "SizeBot Developer")
    async def createroyale(self, ctx, seed = None):
        if current_games[ctx.guild.id]:
            await ctx.send("There is already a game running in this guild!")
            return
        m = await ctx.send("Creating royale...")
        if not ctx.message.attachments:
            m.edit(content = "You didn't upload a royale sheet. Please see https://github.com/DigiDuncan/SizeRoyale/blob/master/royale-spec.txt")
            return
        sheet = ctx.message.attachments[0]
        if not sheet.filename.endswith(".txt"):
            m.edit(content = f"{sheet.filename} is not a `txt` file.")
            return

        current_games[ctx.guild.id] = Game(seed = seed)


def setup(bot):
    bot.add_cog(RoyaleCog(bot))
