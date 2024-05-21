import pydoc
from types import CodeType
from typing import Any
from collections.abc import Callable

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
from discord.ext import commands
import PIL
from PIL import Image, ImageDraw

from sizebot.conf import conf
from sizebot.cogs import thistracker
from sizebot.lib import errors, guilddb, proportions, userdb, utils
from sizebot.lib.constants import emojis, ids
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.diff import Diff, LimitedRate, Rate
from sizebot.lib.loglevels import BANNER, EGG, LOGIN
from sizebot.lib.objs import DigiObject, objects, tags
from sizebot.lib.roller import _evalmath, roll
from sizebot.lib.types import BotContext
from sizebot.lib.units import Mult, SV, TV, WV


logger = logging.getLogger("sizebot")


def _cached_copy(fn: Callable) -> Callable:
    """Decorator that calls the wrapper function the first time it's called, and returns copies of the cached result on all later calls"""
    isCached = False
    r = None

    def wrapper(*args, **kwargs) -> Any:
        nonlocal isCached
        nonlocal r
        if not isCached:
            r = fn(*args, **kwargs)
        isCached = True
        return r.copy()

    return wrapper


@_cached_copy
def get_eval_globals() -> dict[str, Any]:
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
    eval_builtins = {n: (v if n not in blacklist else None) for n, v in vars(builtins).items()}

    eval_globals = {
        "__builtins__": eval_builtins,
        "inspect": inspect,
        "help": str_help,
        "Decimal": Decimal,
        "discord": discord,
        "logging": logging,
        "logger": logger,
        "Mult": Mult, "SV": SV, "WV": WV, "TV": TV,
        "Diff": Diff, "Rate": Rate, "LimitedRate": LimitedRate,
        "DigiObject": DigiObject,
        "objects": objects,
        "tags": tags,
        "utils": utils,
        "pdir": pdir,
        "userdb": userdb,
        "thistracker": thistracker,
        "edir": edir,
        "ids": ids,
        "emojis": emojis,
        "itertools": itertools,
        "conf": conf,
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
        "errors": errors,
        "arrow": arrow,
        "roll": roll,
        "evalmath": _evalmath
    }

    return eval_globals


def _build_eval_wrapper(evalStr: str, addReturn: bool = True) -> tuple[CodeType, str]:
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
            return _build_eval_wrapper(evalStr, False)
        raise

    return evalWrapper, evalWrapperStr


async def run_eval(ctx: BotContext, evalStr: str) -> Any:
    evalGlobals = get_eval_globals()
    evalLocals = {}

    # Add ctx to the globals
    evalGlobals["ctx"] = ctx

    evalWrapper, evalWrapperStr = _build_eval_wrapper(evalStr)

    logger.debug(f"Executing eval:\n{evalWrapperStr}")

    exec(
        evalWrapper,
        evalGlobals,
        evalLocals
    )
    evalFn = evalLocals["__ex"]

    return await evalFn()


def _eformat(name: str, value: Any) -> str:
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
    elif isinstance(value, commands.Bot):
        emojiType = "🤖"
    elif isinstance(value, commands.cog.Cog):
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


def edir(o: Any) -> Embed:
    """send embed of an object's attributes, with type notation"""
    e = Embed(title=get_fullname(o))
    attrs = [_eformat(n, v) for n, v in _ddir(o).items()]
    pageLen = math.ceil(len(attrs) / 3)
    for page in utils.chunk_list(attrs, pageLen):
        e.add_field(value="\n".join(page))
    return e


def _pformat(name: str, value: Any) -> str:
    if value is None:
        return f"{name}?"
    if callable(value):
        return f"{name}()"
    if isinstance(value, (list, tuple)):
        return f"{name}[]"
    if isinstance(value, set):
        return f"{name}{{}}"
    if isinstance(value, dict):
        return f"{name}{{:}}"
    return name


def pdir(o: Any) -> list:
    """return a list of an object's attributes, with type notation."""
    return [_pformat(n, v) for n, v in _ddir(o).items()]


def _ddir(o: Any) -> dict:
    """return a dictionary of an object's attributes."""
    return {n: v for n, v in inspect.getmembers(o) if not n.startswith("_")}


def str_help(topic: str) -> str:
    return pydoc.plain(pydoc.render_doc(topic))


def get_fullname(o: object) -> str:
    moduleName = o.__class__.__module__
    if moduleName == "builtins":
        moduleName = ""
    if moduleName:
        moduleName = f"{moduleName}."

    className = o.__class__.__name__
    fullname = f"{moduleName}{className}"
    return fullname
