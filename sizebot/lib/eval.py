from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from types import CodeType
    from collections.abc import Iterator
    from sizebot.lib.types import BotContext

import logging
import inspect
import math
import re

from mre import Regex, Group
from arrow import Arrow
import pydoc

from discord import Embed, Member, User
from discord.ext import commands

from sizebot.lib.utils import chunk_list
from sizebot.lib.units import SV, TV, WV
import sizebot.lib.discordplusplus as dpp

# Passthrough to eval_globals
import builtins
import io
import itertools
from datetime import date, datetime, time, timedelta
import arrow
import PIL
from PIL import Image, ImageDraw
import discord
from sizebot.conf import conf
from sizebot.cogs import thistracker
from sizebot.lib import errors, guilddb, proportions, userdb, utils
from sizebot.lib.constants import emojis, ids
from sizebot.lib.diff import Diff, LimitedRate, Rate
from sizebot.lib.loglevels import BANNER, EGG, LOGIN
from sizebot.lib.objs import DigiObject, objects, tags
from sizebot.lib.roller import evalmath, roll
from sizebot.lib.units import Mult, Decimal


logger = logging.getLogger("sizebot")


def remove_code_block(s: str) -> str:
    """Extra {code} from a codeblock:

    ```python{code}```
    ```{code}```
    `{code}`
    """
    re_python = Group("python", non_capturing=True).quantifier(0, 1)
    re_code = Group(Regex(Regex.ANY).quantifier(0, without_maximum=True))
    re_codeblock = Regex("```", re_python, re_code, "```")
    re_miniblock = Regex("`", re_code, "`")

    for r in [re_codeblock, re_miniblock]:
        m = re.fullmatch(str(r), s, re.DOTALL)
        if m:
            return m.group(1)

    return s


def eformat(name: str, value: Any) -> str:
    if value is None:
        emoji_type = "❓"
    elif callable(value):
        emoji_type = "🚙"
    elif isinstance(value, list | tuple):
        emoji_type = "🗒️"
    elif isinstance(value, set):
        emoji_type = "📘"
    elif isinstance(value, dict):
        emoji_type = "📗"
    elif isinstance(value, bool):
        if value:
            emoji_type = "✅"
        else:
            emoji_type = "❎"
    elif isinstance(value, int | float):
        emoji_type = "💯"
    elif isinstance(value, str):
        emoji_type = "✏️"
    elif isinstance(value, Member):
        emoji_type = "👥"
    elif isinstance(value, User):
        emoji_type = "👤"
    elif isinstance(value, commands.Bot):
        emoji_type = "🤖"
    elif isinstance(value, commands.Cog):
        emoji_type = "⚙️"
    elif isinstance(value, SV):
        emoji_type = "🇸"
    elif isinstance(value, WV):
        emoji_type = "🇼"
    elif isinstance(value, TV):
        emoji_type = "🇹"
    elif isinstance(value, Arrow):
        emoji_type = "🏹"
    else:
        emoji_type = "▫️"
    return f"{emoji_type} {name}"


def get_fullname(o: object) -> str:
    module_name = o.__class__.__module__
    if module_name == "builtins":
        module_name = ""
    if module_name:
        module_name = f"{module_name}."

    class_name = o.__class__.__name__
    fullname = f"{module_name}{class_name}"
    return fullname


def edir(o: Any) -> Embed:
    """send embed of an object's attributes, with type notation"""
    e = dpp.Embed(title=get_fullname(o))
    attrs = [eformat(n, v) for n, v in ddir(o).items()]
    page_len = math.ceil(len(attrs) / 3)
    for page in chunk_list(attrs, page_len):
        e.add_field(value="\n".join(page))
    return e


def pformat(name: str, value: Any) -> str:
    if value is None:
        return f"{name}?"
    if callable(value):
        return f"{name}()"
    if isinstance(value, list | tuple):
        return f"{name}[]"
    if isinstance(value, set):
        return f"{name}{{}}"
    if isinstance(value, dict):
        return f"{name}{{:}}"
    return name


def pdir(o: Any) -> list[str]:
    """return a list of an object's attributes, with type notation."""
    return [pformat(n, v) for n, v in ddir(o).items()]


def ddir(o: Any) -> dict[str, Any]:
    """return a dictionary of an object's attributes."""
    return {n: v for n, v in inspect.getmembers(o) if not n.startswith("_")}


def str_help(topic: str) -> str:
    return pydoc.plain(pydoc.render_doc(topic))


def find_one[T](iterator: Iterator[T]) -> T | None:
    try:
        val = next(iterator)
    except StopIteration:
        val = None
    return val


def format_error(err: Exception) -> str:
    fullname = get_fullname(err)

    err_message = str(err)
    if err_message:
        err_message = f": {err_message}"

    return f"{fullname}{err_message}"


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
        "findOne": find_one,
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
        "evalmath": evalmath
    }

    return eval_globals


def build_eval_wrapper(eval_str: str, *, add_return: bool) -> tuple[CodeType, str]:
    """Build a wrapping async function that lets the eval command run multiple lines, and return the result of the last line"""
    eval_lines = eval_str.rstrip().split("\n")
    if eval_lines[-1].startswith(" "):
        add_return = False
    if add_return:
        eval_lines[-1] = "return " + eval_lines[-1]
    eval_wrapper_str = "async def __ex():" + "".join(f"\n  {line}" for line in eval_lines)
    eval_wrapper = compile(eval_wrapper_str, "<eval>", "exec")
    return eval_wrapper, eval_wrapper_str


async def run_eval(ctx: BotContext, eval_str: str) -> Embed | str:
    eval_globals = get_eval_globals()
    eval_locals: dict[str, Any] = {}

    # Add ctx to the globals
    eval_globals["ctx"] = ctx
    try:
        eval_wrapper, eval_wrapper_str = build_eval_wrapper(eval_str, add_return=True)
    except SyntaxError:
        eval_wrapper, eval_wrapper_str = build_eval_wrapper(eval_str, add_return=False)

    logger.debug(f"Executing eval:\n{eval_wrapper_str}")

    exec(
        eval_wrapper,
        eval_globals,
        eval_locals
    )
    eval_fn = eval_locals["__ex"]

    result = await eval_fn()

    if isinstance(result, Embed):
        return result
    return str(result).replace("```", r"\`\`\`")
