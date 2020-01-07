import builtins
import pydoc

import discord

from sizebot import digilogger as logger
from sizebot.digiSV import Rate, Mult, SV, WV, TV
import sizebot.utils


# Decorator that calls the wrapper function the first time it's called, and returns copies of the cached result on all later calls
def cachedCopy(fn):
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


def strHelp(topic):
    return pydoc.plain(pydoc.render_doc(topic))


# Construct a globals dict for eval
@cachedCopy
def getEvalGlobals():
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
        "help": strHelp,
        "discord": discord,
        "logger": logger,
        "Rate": Rate, "Mult": Mult, "SV": SV, "WV": WV, "TV": TV,
        "utils": sizebot.utils,
        "pdir": sizebot.utils.pdir
    }

    return evalGlobals


# Build a wrapping async function that lets the eval command run multiple lines, and return the result of the last line
def buildEvalWrapper(evalStr, addReturn = True):
    evalLines = evalStr.split("\n")
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

    await logger.debug(f"Executing eval:\n{evalWrapperStr}")

    exec(
        evalWrapper,
        evalGlobals,
        evalLocals
    )
    evalFn = evalLocals["__ex"]

    return await evalFn()
