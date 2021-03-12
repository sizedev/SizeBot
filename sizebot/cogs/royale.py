import asyncio
import importlib.resources as pkg_resources
import logging
import re
from datetime import timedelta

import arrow

from discord.ext import commands

import sizebot.data
from sizebot.conf import conf
from sizebot.lib import proportions, userdb
from sizebot.lib.constants import emojis, ids
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.errors import DigiException
from sizebot.lib.loglevels import ROYALE
from sizebot.lib.userdb import defaultheight, defaultweight
from sizeroyale import Game
from sizeroyale.lib.errors import GametimeError


logger = logging.getLogger("sizebot")

ok_roles = ["Royale DM", "SizeBot Developer"]


class NoGameFoundError(DigiException):
    def formatMessage(self):
        return "Game not found."


class NoPlayerFoundError(DigiException):
    def __init__(self, player_name):
        self.player_name = player_name

    def formatUserMessage(self):
        return f"Player {self.player_name} not found in this guild's game."


current_games = {}


def get_royale(guildid):
    global current_games
    return None if guildid not in current_games else current_games[guildid]


class RoyaleCog(commands.Cog):
    """Play a game of Size Royale!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    @commands.guild_only()
    async def royale(self, ctx, subcommand, *, args: str = None):
        """
        Size Royale commands.
        `&royale create [seed]`: create a new game in this guild, optionally with a seed.
        Requires a file upload as per https://github.com/DigiDuncan/SizeRoyale/blob/master/royale-spec.txt
        `&royale next [amount]`: Output the next round of events in the game, default 1.
        `&royale overview`: See a stats screen of all players.
        `&royale stats <player>`: Gets stats about a player in the game.
        `&royale compare <player> <player2>`: Compares two players from the game.
        `&royale delete` or `&royale stop`: Deletes the game in this guild (irreversable)
        """
        global current_games

        if subcommand == "create":
            if is_dm(ctx.author) is False:
                return

            arg1, *arg2 = args.split(" ", 1) if args else (None, (None))
            arg2 = arg2[0] if arg2 else None  # This makes split not fail if there's only one element.
            seed = arg1

            if ctx.guild.id in current_games:
                await ctx.send("There is already a game running in this guild!")
                return
            m = await ctx.send("Creating royale...")

            if not ctx.message.attachments and seed != "test":
                await m.edit(content = "You didn't upload a royale sheet. Please see https://github.com/DigiDuncan/SizeRoyale/blob/master/royale-spec.txt")
                return

            if not ctx.message.attachments and seed == "test":
                data = pkg_resources.read_text(sizebot.data, "royale-spec.txt")
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
                        if progress:
                            await m.edit(content = f"`{progress}` {emojis.loading}")
                if game.royale.parser.errors:
                    await ctx.send(f"{emojis.warning} **Errors in parsing:**\n"
                                   + ("\n".join(game.royale.parser.errors)))
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
            arg1 = args

            if is_dm(ctx.author) is False:
                return

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
                    # PERMISSION: requires attach_file
                    await ctx.send(embed = data[0], file = data[1])
                    await asyncio.sleep(1)

        elif subcommand == "overview":
            stats = await current_games[ctx.guild.id].stats_screen()
            data = stats.to_embed()
            # PERMISSION: requires attach_file
            await ctx.send(embed = data[0], file = data[1])

        elif subcommand == "stop" or subcommand == "delete":
            if is_dm(ctx.author) is False:
                return

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

        elif subcommand == "stats":
            arg1 = args

            if arg1.startswith("\"") and arg1.endswith("\""):
                player = arg1[1:-1]
            else:
                await ctx.send(f"Player names must be in quotes. e.g.: `{conf.prefix}royale stats \"DigiDuncan\"`.")
                return

            userdata = getPlayerData(ctx.guild.id, player)

            stats = proportions.PersonStats(userdata)

            embedtosend = stats.toEmbed(ctx.author.id)
            await ctx.send(embed = embedtosend)

            logger.log(ROYALE, f"Stats for {player} sent.")

        elif subcommand == "compare":
            arg1 = args

            if match := re.match(r"\"(.*)\"\s*\"(.*)\"", arg1):
                player1 = match.group(1)
                player2 = match.group(2)
            else:
                await ctx.send(f"Player names must be in quotes. e.g.: `{conf.prefix}royale compare \"DigiDuncan\" \"Kelly\"`.")
                return

            userdata1 = getPlayerData(player1)
            userdata2 = getPlayerData(player2)

            comparison = proportions.PersonComparison(userdata1, userdata2)
            embedtosend = await comparison.toEmbed(ctx.author.id)
            await ctx.send(embed = embedtosend)

        elif subcommand == "create":
            pass  # Fixed "invalid subcommand create" on tests

        else:
            await ctx.send(f"Invalid subcommand `{subcommand}` for royale.")


def is_dm(user) -> bool:
    for role in ok_roles:
        if role in user.rolelist:
            return True
    return False


def getPlayerData(guild: int, player: str) -> userdb.User:
    if guild not in current_games:
        raise NoGameFoundError
    if player not in current_games[guild].royale.players or player is None:
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
