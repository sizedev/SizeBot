import builtins
import inspect
import io
import itertools
import logging
import math
from datetime import date, datetime, time, timedelta

import arrow
import discord
from discord import Embed
import PIL
from PIL import Image, ImageDraw

from sizebot.conf import conf
from sizebot.cogs import royale, thistracker
from sizebot.cogs.royale import get_royale
from sizebot.lib import errors, guilddb, proportions, userdb, utils
from sizebot.lib.constants import emojis, ids
from sizebot.lib.decimal import Decimal
from sizebot.lib.diff import Diff, LimitedRate
from sizebot.lib.diff import Rate as ParseableRate
from sizebot.lib.loglevels import BANNER, EGG, LOGIN
from sizebot.lib.objs import objects
from sizebot.lib.units import Rate, Mult, SV, TV, WV


logger = logging.getLogger("sizebot")


def eformat(name, value):
    if value is None:
        emojiType = "❓"
    elif callable(value):
        emojiType = "🚙"
    elif isinstance(value, (list, tuple)):
        emojiType = "🗒️"
    elif isinstance(value, set):
        emojiType = "📘"
    elif isinstance(value, dict):
        emojiType = "📗"
    elif isinstance(value, bool):
        if value:
            emojiType = "✅"
        else:
            emojiType = "❎"
    elif isinstance(value, (int, float)):
        emojiType = "💯"
    elif isinstance(value, str):
        emojiType = "✏️"
    elif isinstance(value, discord.member.Member):
        emojiType = "👥"
    elif isinstance(value, discord.user.User):
        emojiType = "👤"
    elif isinstance(value, discord.ext.commands.Bot):
        emojiType = "🤖"
    elif isinstance(value, discord.ext.commands.cog.Cog):
        emojiType = "⚙️"
    elif isinstance(value, SV):
        emojiType = "🇸"
    elif isinstance(value, WV):
        emojiType = "🇼"
    elif isinstance(value, TV):
        emojiType = "🇹"
    elif isinstance(value, arrow.arrow.Arrow):
        emojiType = "🏹"
    else:
        emojiType = "▫️"
    return f"{emojiType} {name}"


def edir(o):
    """send embed of an object's attributes, with type notation"""
    e = Embed(title=utils.getFullname(o))
    attrs = [eformat(n, v) for n, v in utils.ddir(o).items()]
    pageLen = math.ceil(len(attrs) / 3)
    for page in utils.chunkList(attrs, pageLen):
        e.add_field(value="\n".join(page))
    return e


def cachedCopy(fn):
    """Decorator that calls the wrapper function the first time it's called, and returns copies of the cached result on all later calls"""
    isCached = False
    r = None

    def wrapper(*args, **kwargs):
        nonlocal isCached
        nonlocal r
        if not isCached:
            r = fn(*args, **kwargs)
        isCached = True
        return r.copy()

    return wrapper


@cachedCopy
def getEvalGlobals():
    """Construct a globals dict for eval"""
    # Create a dict of builtins, excluding any in the blacklist
    blacklist = [
        "breakpoint",
        "classmethod",
        "compile",
        "eval",
        "exec",
        "help",
        "input",
        "memoryview",
        "open",
        "print",
        "staticmethod",
        "super",
        "__import__"
    ]
    evalBuiltins = {n: (v if n not in blacklist else None) for n, v in vars(builtins).items()}

    evalGlobals = {
        "__builtins__": evalBuiltins,
        "inspect": inspect,
        "help": utils.strHelp,
        "Decimal": Decimal,
        "discord": discord,
        "logging": logging,
        "logger": logger,
        "Rate": Rate, "Mult": Mult, "SV": SV, "WV": WV, "TV": TV,
        "Diff": Diff, "ParseableRate": ParseableRate, "LimitedRate": LimitedRate,
        "objects": objects,
        "utils": utils,
        "pdir": utils.pdir,
        "userdb": userdb,
        "thistracker": thistracker,
        "edir": edir,
        "ids": ids,
        "emojis": emojis,
        "itertools": itertools,
        "conf": conf,
        "findOne": utils.findOne,
        "datetime": datetime,
        "date": date,
        "time": time,
        "timedelta": timedelta,
        "math": math,
        "BANNER": BANNER, "EGG": EGG, "LOGIN": LOGIN,
        "guilddb": guilddb,
        "proportions": proportions,
        "PIL": PIL,
        "Image": Image,
        "ImageDraw": ImageDraw,
        "io": io,
        "logger": logger,
        "get_royale": get_royale,
        "royale": royale,
        "errors": errors,
        "arrow": arrow
    }

    return evalGlobals


def buildEvalWrapper(evalStr, addReturn = True):
    """Build a wrapping async function that lets the eval command run multiple lines, and return the result of the last line"""
    evalLines = evalStr.rstrip().split("\n")
    if evalLines[-1].startswith(" "):
        addReturn = False
    if addReturn:
        evalLines[-1] = "return " + evalLines[-1]
    evalWrapperStr = "async def __ex():" + "".join(f"\n  {line}" for line in evalLines)
    try:
        evalWrapper = compile(evalWrapperStr, "<eval>", "exec")
    except SyntaxError:
        # If we get a syntax error, maybe it's because someone is trying to do an assignment on the last line? Might as well try it without a return statement and see if it works.
        if addReturn:
            return buildEvalWrapper(evalStr, False)
        raise

    return evalWrapper, evalWrapperStr


async def runEval(ctx, evalStr):
    evalGlobals = getEvalGlobals()
    evalLocals = {}

    # Add ctx to the globals
    evalGlobals["ctx"] = ctx

    evalWrapper, evalWrapperStr = buildEvalWrapper(evalStr)

    logger.debug(f"Executing eval:\n{evalWrapperStr}")

    exec(
        evalWrapper,
        evalGlobals,
        evalLocals
    )
    evalFn = evalLocals["__ex"]

    return await evalFn()
