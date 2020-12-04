import asyncio
from datetime import timedelta
from pathlib import Path


import arrow

from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.constants import emojis, ids
from sizebot.lib.decimal import Decimal
from sizebot.lib.errors import DigiException
from sizebot.lib.userdb import defaultheight, defaultweight
from sizeroyale import Game
from sizeroyale.lib.errors import GametimeError


class NoGameFoundError(DigiException):
    async def formatMessage(self):
        return "Game not found."


class NoPlayerFoundError(DigiException):
    def __init__(self, player_name):
        self.player_name = player_name

    async def formatMessage(self):
        return f"Player {self.player_name} not found."


current_games = {}


class RoyaleCog(commands.Cog):
    """Play a game of Size Royale!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    @commands.has_any_role("Royale DM", "SizeBot Developer")
    async def royale(self, ctx, subcommand, arg1 = None, arg2 = None):
        if subcommand == "create":
            seed = arg1

            if ctx.guild.id in current_games:
                await ctx.send("There is already a game running in this guild!")
                return
            m = await ctx.send("Creating royale...")

            if not ctx.message.attachments and seed != "test":
                await m.edit(content = "You didn't upload a royale sheet. Please see https://github.com/DigiDuncan/SizeRoyale/blob/master/royale-spec.txt")
                return

            if not ctx.message.attachments and seed == "test":
                with open(Path(__file__).parent.parent.parent / "royale-spec.txt") as f:
                    data = f.read()
                filename = "test"
                seed = arg2 if arg2 else "radically-key-gazelle"
            else:
                sheet = ctx.message.attachments[0]
                filename = sheet.filename
                if not sheet.filename.endswith(".txt"):
                    await m.edit(content = f"{sheet.filename} is not a `txt` file.")
                    return
                data = (await sheet.read()).decode("utf-8")

            game = Game(seed = seed)
            loop = arrow.now()
            try:
                async for progress in await game.load(data):
                    looppoint = arrow.now()
                    if looppoint - loop >= timedelta(seconds = 1):
                        loop = looppoint
                        await m.edit(content = f"`{progress}` {emojis.loading}")
                if game.royale.parser.errors:
                    await ctx.send(f"{emojis.warning} **Errors in parsing:**\n"
                                   "\n".join(game.royale.parser.errors))
                    return
                current_games[ctx.guild.id] = game
                await m.edit(content = f"Royale loaded with file `{filename}` and seed `{current_games[ctx.guild.id].seed}`.")
            except Exception:
                await m.edit(content = "Game failed to load.")
                raise

        else:
            if ctx.guild.id not in current_games:
                await ctx.send("There is no game running in this guild!")
                return

        if subcommand == "next":
            loops = int(arg1) if arg1 else 1

            for i in range(loops):
                try:
                    round = await current_games[ctx.guild.id].next()
                except GametimeError as e:
                    await ctx.send(f"Error in running event: {e}")
                    await ctx.send(f"Please check your game file and consider contacting <@{ids.digiduncan}>.")
                    return
                for e in round:
                    data = e.to_embed()
                    await ctx.send(embed = data[0], file = data[1])
                    await asyncio.sleep(1)

        elif subcommand == "overview":
            stats = await current_games[ctx.guild.id].stats_screen()
            data = stats.to_embed()
            await ctx.send(embed = data[0], file = data[1])

        elif subcommand == "stop" or subcommand == "delete":
            sentMsg = await ctx.send(f"{emojis.warning} **WARNING!** Deleting your game will remove *all progress irrecoverably.* Are you sure?"
                                     f"To delete your game, react with {emojis.check}.")
            await sentMsg.add_reaction(emojis.check)
            await sentMsg.add_reaction(emojis.cancel)

            # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
            def check(reaction, reacter):
                return reaction.message.id == sentMsg.id \
                    and reacter.id == ctx.message.author.id \
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

        elif subcommand == "create":
            pass  # Fixed "invalid subcommand create" on tests

        else:
            await ctx.send(f"Invalid subcommand `{subcommand}` for royale.")


def getPlayerData(guild: int, player: str) -> userdb.User:
    if guild not in current_games:
        raise NoGameFoundError
    if player not in current_games[guild].royale.players:
        raise NoPlayerFoundError(player)

    userdata = userdb.User()
    p = current_games[guild].royale.players[player]

    userdata.baseheight = p.baseheight
    userdata.baseweight = defaultweight * ((p.baseheight / defaultheight) ** 3)
    userdata.height = p.height
    userdata.nickname = p.name
    userdata.gender = p.gender
    if "paw" in p.attributes or "paws" in p.attributes:
        userdata.pawtoggle = True
    if "fur" in p.attributes:
        userdata.furtoggle = True
    if "tail" in p.attributes:
        userdata.taillength = p.height * Decimal("94169/150000")

    return userdata


def setup(bot):
    bot.add_cog(RoyaleCog(bot))
