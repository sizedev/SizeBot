import inspect
import math
import builtins
import itertools
from decimal import Decimal

import discord
from discord.ext import commands

import sizebot.digilogger as logger
from sizebot import utils
from sizebot import globalsb

emojis = {
    "loading": "Loading...",
    "warning": "⚠️"
}


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
    else:
        emojiType = "▫️"
    return f"{emojiType} {name}"


def edir(o):
    """send embed of an object's attributes, with type notation"""
    e = discord.Embed(title=utils.getFullname(o))
    attrs = [eformat(n, v) for n, v in utils.ddir(o).items()]
    pageLen = math.ceil(len(attrs) / 3)
    for page in utils.chunkList(attrs, pageLen):
        e.add_field(name="\u200b", value="\n".join(page))
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
        "Decimal": Decimal,
        "discord": discord,
        "logger": logger,
        "edir": edir,
        "itertools": itertools,
        "utils": utils,
        "globalsb": globalsb
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

    logger.load(f"Executing eval:\n{evalWrapperStr}")

    exec(
        evalWrapper,
        evalGlobals,
        evalLocals
    )
    evalFn = evalLocals["__ex"]

    return await evalFn()


class EvalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def eval(self, ctx, *, evalStr):
        """Evaluate a Python expression."""
        evalStr = utils.removeCodeBlock(evalStr)

        logger.msg(f"{ctx.message.author.display_name} tried to eval {evalStr!r}.")

        # Show user that bot is busy doing something
        waitMsg = None
        if isinstance(ctx.channel, discord.TextChannel):
            waitMsg = await ctx.send(emojis["loading"])

        async with ctx.typing():
            try:
                result = await runEval(ctx, evalStr)
            except Exception as err:
                logger.crit("eval error:\n" + utils.formatTraceback(err))
                await ctx.send(emojis["warning"] + f" ` {utils.formatError(err)} `")
                return
            finally:
                # Remove wait message when done
                if waitMsg:
                    await waitMsg.delete(delay=0)

        if isinstance(result, discord.Embed):
            await ctx.send(embed=result)
        else:
            strResult = str(result).replace("```", r"\`\`\`")
            for m in utils.chunkMsg(strResult):
                await ctx.send(m)

    @commands.command(
        hidden = True
    )
    @commands.is_owner()
    async def evil(self, ctx, *, evalStr):
        """Evaluate a Python expression, but evilly."""
        await ctx.message.delete(delay = 0)

        evalStr = utils.removeCodeBlock(evalStr)

        logger.msg(f"{ctx.message.author.display_name} tried to quietly eval {evalStr!r}.")

        async with ctx.typing():
            try:
                await runEval(ctx, evalStr, returnValue = False)
            except Exception as err:
                logger.crit("eval error:\n" + utils.formatTraceback(err))
                await ctx.message.author.send("**!**" + f" ` {utils.formatError(err)} `")


def setup(bot):
    bot.add_cog(EvalCog(bot))
