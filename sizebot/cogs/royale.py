from datetime import timedelta
import arrow

from discord.ext import commands

from sizeroyale import Game


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
        if ctx.guild.id in current_games:
            await ctx.send("There is already a game running in this guild!")
            return
        m = await ctx.send("Creating royale...")
        if not ctx.message.attachments:
            await m.edit(content = "You didn't upload a royale sheet. Please see https://github.com/DigiDuncan/SizeRoyale/blob/master/royale-spec.txt")
            return
        sheet = ctx.message.attachments[0]
        if not sheet.filename.endswith(".txt"):
            await m.edit(content = f"{sheet.filename} is not a `txt` file.")
            return

        f = (await sheet.read()).decode("utf-8")
        current_games[ctx.guild.id] = Game(seed = seed)
        loop = arrow.now()
        for progress in current_games[ctx.guild.id].load(f):
            looppoint = arrow.now()
            if looppoint - loop >= timedelta(seconds = 1):
                loop = looppoint
                await m.edit(content = progress)
        await m.edit(content = f"Royale loaded with file `{sheet.filename}` and seed `{current_games[ctx.guild.id].seed}`.")


def setup(bot):
    bot.add_cog(RoyaleCog(bot))
