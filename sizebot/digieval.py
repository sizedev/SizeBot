import builtins
import pydoc

from sizebot import digilogger as logger
from sizebot import digiSV
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
    return pydoc.render_doc(topic)


# Construct a globals dict for eval
@cachedCopy
def getEvalGlobals():
    # Collect all safe builtins to include (whitelist)
    # Removed builtins: breakpoint, classmethod, compile, eval, exec, help, input, memoryview, open, print, staticmethod, super
    safeBuiltins = ["abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes", "callable", "chr", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "filter", "float", "format", "frozenset", "getattr", "globals", "hasattr", "hash", "hex", "id", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "min", "next", "object", "oct", "ord", "pow", "property", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "str", "sum", "tuple", "type", "vars", "zip", "__import__"]
    custom_builtins = {"help": strHelp}
    evalBuiltins = {b: getattr(builtins, b) for b in safeBuiltins}
    evalBuiltins.update(custom_builtins)

    # Collect all libraries to include
    evalImports = {"pydoc": pydoc, "logger": logger, "digiSV": digiSV, "utils": sizebot.utils, "pdir": sizebot.utils.pdir}

    evalGlobals = {"__builtins__": evalBuiltins}
    evalGlobals.update(evalImports)

    return evalGlobals


# Build a wrapping async function that lets the eval command run multiple lines, and return the result of the last line
def buildEvalWrapper(evalStr):
    evalLines = evalStr.split("\n")
    evalLines[-1] = "return " + evalLines[-1]
    evalWrapperStr = "async def __ex():\n" + "".join(f"\n    {line}" for line in evalLines)
    evalWrapper = compile(evalWrapperStr, "<eval>", "exec")
    return evalWrapper


async def runEval(ctx, evalStr):
    evalGlobals = getEvalGlobals()
    evalLocals = {}

    # Add ctx to the globals
    evalGlobals["ctx"] = ctx

    evalWrapper = buildEvalWrapper(evalStr)

    exec(
        evalWrapper,
        evalGlobals,
        evalLocals
    )
    evalFn = evalLocals["__ex"]

    return await evalFn()
