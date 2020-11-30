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

        else:
            if not ctx.guild.id in current_games:
                await ctx.send("There is no game running in this guild!")
                return
        
        if subcommand == "next":
            round = await current_games[ctx.guild.id].next()
            for e in round:
                data = e.to_embed()
                await ctx.send(embed = data[0], file = data[1])
                await asyncio.sleep(1)

        if subcommand == "overview":
            data = current_games[ctx.guild.id].stats_screen().to_embed()
            await ctx.send(embed = data[0], file = data[1])

        if subcommand == "stop" or subcommand == "delete":
            sentMsg = await ctx.send(f"{emojis.warning} **WARNING!** Deleting your game will remove *all progress irrecoverably.* Are you sure?"
                f"To delete your game, react with {emojis.check}.")
            await sentMsg.add_reaction(emojis.check)
            await sentMsg.add_reaction(emojis.cancel)

            # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
            def check(reaction, reacter):
                return reaction.message.id == sentMsg.id \
                    and reacter.id == user.id \
                    and (
                        str(reaction.emoji) == emojis.check
                        or str(reaction.emoji) == emojis.cancel
                    )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                # User took too long to respond
                return
            finally:
                # User took too long OR User clicked the emoji
                await sentMsg.delete()

            # if the reaction isn't the right one, stop.
            if reaction.emoji != emojis.check:
                return

            current_games.pop(ctx.guild.id)

def setup(bot):
    bot.add_cog(RoyaleCog(bot))
