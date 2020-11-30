import asyncio
from datetime import timedelta
import arrow

from discord.ext import commands

from sizebot.lib.constants import emojis
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
    async def royale(self, ctx, subcommand, arg1 = None):
        if subcommand == "create":
            seed = arg1

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
            game = Game(seed = seed)
            loop = arrow.now()
            try:
                async for progress in await game.load(f):
                    looppoint = arrow.now()
                    if looppoint - loop >= timedelta(seconds = 1):
                        loop = looppoint
                        await m.edit(content = f"`{progress}` {emojis.loading}")
                current_games[ctx.guild.id] = game
                await m.edit(content = f"Royale loaded with file `{sheet.filename}` and seed `{current_games[ctx.guild.id].seed}`.")
            except Exception:
                await m.edit(content = f"Game failed to load.")
                raise
        
        elif subcommand == "next":
            if not ctx.guild.id in current_games:
                await ctx.send("There is no game running in this guild!")
                return
            round = await current_games[ctx.guild.id].next()
            for e in round:
                await ctx.send(embed = e.to_embed())
                await asyncio.sleep(1)

def setup(bot):
    bot.add_cog(RoyaleCog(bot))
