import logging

from discord.ext import commands, tasks

from sizebot.lib import naps, utils
from sizebot.lib.types import BotContext
from sizebot.lib.units import TV

logger = logging.getLogger("sizebot")


class NaptimeCog(commands.Cog):
    """Commands for napping."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.nannyTask.start()

    def cog_unload(self):
        self.nannyTask.cancel()

    @commands.command(
        aliases = ["chloroform"],
        usage = "<duration>",
        category = "fun"
    )
    @commands.guild_only()
    async def naptime(self, ctx: BotContext, *, duration: TV):
        """Go to bed in a set amount of time.

        Kicks you from any voice channel you're in after a set amount of time.
        """
        # TODO: Disable and hide this command on servers where bot does not have MOVE_MEMBERS permission
        if not ctx.me.guild_permissions.move_members:
            await ctx.send("Sorry, I don't have permission to kick users from voice channels")
            return

        logger.info(f"{ctx.author.display_name} wants to go to sleep in {duration:m}.")

        naps.start(ctx.author.id, ctx.guild.id, duration)

        await ctx.send(f"See you in {duration:m}!")

    @commands.command(
        category = "fun"
    )
    async def grump(self, ctx: BotContext):
        """Too grumpy for bed time.

        Stops a &naptime command.
        """
        logger.info(f"{ctx.author.display_name} wants to cancel bedtime.")

        nanny = naps.stop(ctx.author.id)
        if nanny is not None:
            await ctx.send("Naptime has been cancelled.")

    @commands.command(
        aliases = ["nanny"],
        hidden = True,
        category = "mod"
    )
    @commands.is_owner()
    async def nannies(self, ctx: BotContext):
        """Show me those nannies!"""
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)

        nannyDump = naps.format_summary()

        if not nannyDump:
            nannyDump = "No active nannies."

        await ctx.author.send("**WAITING NANNIES**\n" + nannyDump)
        logger.info(f"User {ctx.author.id} ({ctx.author.display_name}) dumped the waiting nannies.")

    # TODO: CamelCase
    @tasks.loop(seconds=60)
    async def nannyTask(self):
        """Nanny task"""
        try:
            await naps.check(self.bot)
        except Exception as e:
            logger.error("Ignoring exception in nannyTask")
            logger.error(utils.format_traceback(e))


async def setup(bot: commands.Bot):
    await bot.add_cog(NaptimeCog(bot))
