import random
import re

import numexpr

from sizebot.lib import errors


def evalmath(expression):
    return int(numexpr.evaluate(expression, local_dict={}, global_dict={}))


class RollArg:
    __slots__ = ["rolls", "sides", "drop"]
    re_pattern = re.compile(r"(\d+)d(\d+)(?:([dk])(\d+))?")
    re_pattern_all = re.compile(r"(\d+d\d+(?:[dk]\d+)?)")

    def __init__(self, rolls, sides, drop=0):
        self.rolls = rolls
        self.sides = sides
        self.drop = drop

    def roll(self):
        # roll the dice
        rolls = [random.randint(1, self.sides) for _ in range(self.rolls)]
        # get list of lowest dice to drop
        lowest = sorted(rolls)[:self.drop]
        # make lists of used and dropped rolls, in the order they were rolled
        used = []
        dropped = []
        for r in rolls:
            if r in lowest:
                lowest.remove(r)
                dropped.append(r)
            else:
                used.append(r)
        return RollResult(used, dropped)

    @classmethod
    def parse(cls, s):
        match = cls.re_pattern.match(s)
        if match is None:
            return None
        rolls = int(match.group(1))
        sides = int(match.group(2))
        dropmode = match.group(3)
        dropcount = 0
        if dropmode is not None:
            dropcount = int(match.group(4))
            if dropmode == "k":
                dropcount = rolls - dropcount
            dropcount = max(0, min(dropcount, rolls))
        return cls(rolls, sides, dropcount)


class RollResult:
    __slots__ = ["total", "used", "dropped"]

    def __init__(self, used, dropped):
        self.total = sum(used)
        self.used = used
        self.dropped = dropped

    def __str__(self):
        output = (f"    Total: {self.total}\n"
                  f"    Used: {self.used}\n")
        if len(self.dropped) > 0:
            output += f"    Dropped: {self.dropped}\n"
        return output


class Result:
    def __init__(self, total, rolls):
        self.total = total
        self.rolls = rolls

    def __str__(self):
        output = (f"Total: {self.total}\n"
                  f"Rolls:\n")
        for i, r in enumerate(self.rolls):
            output += (f"Roll {i+1}:\n"
                       f"{r}")
        return output


def roll(argstring):
    # Split up and categorize parameters
    argstrings = RollArg.re_pattern_all.split(argstring)
    rolls = []
    rollexpr = ""
    for s in argstrings:
        rollarg = RollArg.parse(s)
        if rollarg is not None:
            result = rollarg.roll()
            rolls.append(result)
            s = result.total
        rollexpr += str(s)

    try:
        total = evalmath(rollexpr)
    except Exception:
        raise errors.InvalidRollException(argstring)

    return Result(total, rolls)
