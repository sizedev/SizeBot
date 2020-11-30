from discord.ext import commands

current_game = None


class RoyaleCog(commands.Cog):
    """Play a game of Size Royale!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    async def createroyale(self, ctx, seed = None):
        m = await ctx.send("Creating royale...")
        if not ctx.message.attachments:
            m.edit(content = "You didn't upload a royale sheet. Please see https://github.com/DigiDuncan/SizeRoyale/blob/master/royale-spec.txt")
            return
        sheet = ctx.message.attachments[0]
        if not sheet.filename.endswith(".txt"):
            m.edit(content = f"{sheet.filename} is not a `txt` file.")
            return


def setup(bot):
    bot.add_cog(RoyaleCog(bot))
