import importlib.resources as pkg_resources
import logging
import random
from typing import cast
from sizebot.lib import errors, utils
from sizebot.lib.digidecimal import Decimal

from discord import Member
from discord.ext import commands, tasks

import sizebot.data
from sizebot.lib import changes, userdb, nickmanager
from sizebot.lib.diff import Diff, LimitedRate, Rate
from sizebot.lib.errors import ChangeMethodInvalidException
from sizebot.lib.objs import DigiObject, objects
from sizebot.lib.types import BotContext, StrToSend
from sizebot.lib.units import SV

logger = logging.getLogger("sizebot")


def _change_user(guildid: int, userid: int, changestyle: str, amount: SV):
    changestyle = changestyle.lower()
    if changestyle in ["add", "+", "a", "plus"]:
        changestyle = "add"
    if changestyle in ["subtract", "sub", "-", "minus"]:
        changestyle = "subtract"
    if changestyle in ["power", "exp", "pow", "exponent", "^", "**"]:
        changestyle = "power"
    if changestyle in ["multiply", "mult", "m", "x", "times", "*"]:
        changestyle = "multiply"
    if changestyle in ["divide", "d", "/", "div"]:
        changestyle = "divide"
    if changestyle in ["percent", "per", "perc", "%"]:
        changestyle = "percent"

    if changestyle not in ["add", "subtract", "multiply", "divide", "power", "percent"]:
        raise errors.ChangeMethodInvalidException(changestyle)

    amountSV = None
    amountVal = None
    newamount = None

    if changestyle in ["add", "subtract"]:
        amountSV = SV.parse(amount)
    elif changestyle in ["multiply", "divide", "power"]:
        amountVal = Decimal(amount)
        if amountVal == 1:
            raise errors.ValueIsOneException
        if amountVal == 0:
            raise errors.ValueIsZeroException
    elif changestyle in ["percent"]:
        amountVal = Decimal(amount)
        if amountVal == 0:
            raise errors.ValueIsZeroException

    userdata = userdb.load(guildid, userid)

    if changestyle == "add":
        newamount = userdata.height + amountSV
    elif changestyle == "subtract":
        newamount = userdata.height - amountSV
    elif changestyle == "multiply":
        newamount = userdata.height * amountVal
    elif changestyle == "divide":
        newamount = userdata.height / amountVal
    elif changestyle == "power":
        userdata = userdata ** amountVal
    elif changestyle == "percent":
        newamount = userdata.height * (amountVal / 100)

    if changestyle != "power":
        userdata.height = newamount

    userdb.save(userdata)


def _stop_changes(user: Member) -> StrToSend:
    deleted = changes.stop(user.id, user.guild.id)
    if deleted is None:
        return {"content": "You can't stop slow-changing, as you don't have a task active!"}
    return {"content": f"{user.display_name} has stopped slow-changing."}


class ChangeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        changes.load_from_file()

    @commands.Cog.listener()
    async def on_first_ready(self):
        # Don't start the change tasks until the bot is properly connected
        self.change_task.start()

    def cog_unload(self):
        self.change_task.cancel()

    @commands.command(
        aliases = ["c"],
        category = "change",
        usage = "<change> [rate] [stop]"
    )
    async def change(self, ctx: BotContext, *, arg: LimitedRate | Rate | Diff | str):
        """Either change or slow-change your height.

        Can be used in essentially the three following ways:
        `&change <amount>`
        `&change <amount>/<time>`
        `&change <amount>/<time> until <size/time>`

        Examples:
        `&change +1ft`
        `&change *2`
        `&change 50ft/day`
        `&change -1in/min until 1ft`
        `&change -1mm/sec for 1hr`
        """
        guildid = ctx.guild.id
        userid = ctx.author.id
        userdata = userdb.load(guildid, userid)  # Load this data but don't use it as an ad-hoc user test.

        if isinstance(arg, Diff):
            style = arg.changetype
            amount = arg.amount

            if style == "add":
                userdata.height = userdata.height + cast(SV, amount)
            elif style == "multiply":
                userdata.height = userdata.height * cast(Decimal, amount)
            elif style == "power":
                userdata.scale = userdata.scale ** cast(Decimal, amount)
            else:
                raise ChangeMethodInvalidException(style)
            await nickmanager.nick_update(ctx.author)
            userdb.save(userdata)
            await ctx.send(f"{userdata.nickname} is now {userdata.height:m} ({userdata.height:u}) tall.")
        elif isinstance(arg, Rate) or isinstance(arg, LimitedRate):
            changes.start(userid, guildid, addPerSec=arg.addPerSec, mulPerSec=arg.mulPerSec, stopSV=arg.stopSV, stopTV=arg.stopTV)
            await ctx.send(f"{ctx.author.display_name} has begun slow-changing at a rate of `{str(arg)}`.")
        elif arg == "stop":
            await ctx.send(**_stop_changes(ctx.author))

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def changes(self, ctx: BotContext):
        # PERMISSION: requires manage_messages
        await ctx.message.delete(delay=0)

        changeDump = changes.format_summary()

        if not changeDump:
            changeDump = "No active changes"

        await ctx.author.send("**ACTIVE CHANGES**\n" + changeDump)

    @commands.command(
        aliases = ["changestop"],
        category = "change"
    )
    @commands.guild_only()
    async def stopchange(self, ctx: BotContext):
        """Stop a currently active slow change."""
        await ctx.send(**_stop_changes(ctx.author))

    @commands.command(
        aliases = ["eat"],
        category = "change"
    )
    @commands.guild_only()
    async def eatme(self, ctx: BotContext):
        """Eat me!

        Increases your height by a random amount between 2x and 20x."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        randmult = round(random.randint(2, 20), 1)
        _change_user(guildid, userid, "multiply", randmult)
        await nickmanager.nick_update(ctx.author)
        userdata = userdb.load(guildid, userid)

        lines = pkg_resources.read_text(sizebot.data, "eatme.txt").splitlines()
        line = random.choice(lines)

        await ctx.send(
            f"{userdata.nickname} ate a :cake:! *{line}*\n"
            f"They multiplied {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")

    @commands.command(
        aliases = ["drink"],
        category = "change"
    )
    @commands.guild_only()
    async def drinkme(self, ctx: BotContext):
        """Drink me!

        Decreases your height by a random amount between 2x and 20x."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        randmult = round(random.randint(2, 20), 1)
        _change_user(guildid, ctx.author.id, "divide", randmult)
        await nickmanager.nick_update(ctx.author)
        userdata = userdb.load(guildid, userid)

        lines = pkg_resources.read_text(sizebot.data, "drinkme.txt").splitlines()
        line = random.choice(lines)

        await ctx.send(
            f"{userdata.nickname} drank a :milk:! *{line}*\n"
            f"They shrunk {randmult}x and are now {userdata.height:m} tall. ({userdata.height:u})")

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def pushme(self, ctx: BotContext):
        """Push me!

        Increases or decreases your height by a random amount between 2x and 20x."""
        c = random.randint(1, 2)
        if c == 1:
            await ctx.invoke(self.bot.get_command("eatme"))
        else:
            await ctx.invoke(self.bot.get_command("drinkme"))

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def outgrow(self, ctx: BotContext, *, obj: DigiObject | None = None):
        """Outgrows the next object in the object database, or an object you specify."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        if obj is None:
            objs_larger = [o for o in objects if o.unitlength > userdata.height]
            if not objs_larger:
                await ctx.send("You have nothing left to outgrow!")
                return
            obj = objs_larger[0]

        if obj.unitlength < userdata.height:
            await ctx.send(f"You're already larger than {obj.article} {obj.name}!")
            return

        random_factor = Decimal(random.randint(11, 20) / 10)
        userdata.height = SV(obj.unitlength * random_factor)
        userdb.save(userdata)

        await ctx.send(f"You outgrew {obj.article} **{obj.name}** *({obj.unitlength:,.3mu})* and are now **{userdata.height:,.3mu}** tall!")

    @commands.command(
        category = "change"
    )
    @commands.guild_only()
    async def outshrink(self, ctx: BotContext, *, obj: DigiObject | None = None):
        """Outshrinks the next object in the object database or an object you specify."""
        guildid = ctx.guild.id
        userid = ctx.author.id

        userdata = userdb.load(guildid, userid)
        if obj is None:
            objs_smaller = [o for o in objects if o.unitlength < userdata.height]
            objs_smaller.reverse()
            if not objs_smaller:
                await ctx.send("You have nothing left to outshrink!")
                return
            obj = objs_smaller[0]

        if obj.unitlength > userdata.height:
            await ctx.send(f"You're already smaller than {obj.article} {obj.name}!")
            return

        random_factor = Decimal(random.randint(11, 20) / 10)
        userdata.height = SV(obj.unitlength / random_factor)
        userdb.save(userdata)

        await ctx.send(f"You outshrunk {obj.article} **{obj.name}** *({obj.unitlength:,.3mu})* and are now **{userdata.height:,.3mu}** tall!")

    @tasks.loop(seconds=6)
    async def change_task(self):
        """Slow growth task"""
        try:
            await changes.apply(self.bot)
        except Exception as e:
            logger.error("Ignoring exception in change_task")
            logger.error(utils.format_traceback(e))


async def setup(bot: commands.Bot):
    await bot.add_cog(ChangeCog(bot))
