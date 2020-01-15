import re
import decimal
import random

__all__ = ["Decimal", "roundDecimal", "fixZeroes", "randRangeLog", "parseSpec", "buildSpec"]

# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


class Decimal(decimal.Decimal):
    def __format__(self, spec):
        value = decimal.Decimal(self)
        formatDict = parseSpec(spec)

        fractional = formatDict["fractional"]
        formatDict["fractional"] = None
        try:
            denom = int(fractional[1])
        except IndexError:
            denom = 8

        if Decimal("1e-10") < value < Decimal("1e10"):
            fraction = ""
            if fractional:
                formatDict["precision"] = "0"
                value, fraction = splitFraction(value, denom)

            formatDict["type"] = "f"
            numspec = buildSpec(formatDict)
            formatted = format(fixZeroes(value), numspec)

            if fraction:
                if formatted == "0":
                    formatted = ""
                formatted += fraction
        else:
            formatDict["type"] = "e"
            numspec = buildSpec(formatDict)
            formatted = format(fixZeroes(value), numspec)

        return formatted


formatSpecRe = re.compile(r"""\A
(?:
   (?P<fill>.)?
   (?P<align>[<>=^])
)?
(?P<sign>[-+ ])?
(?P<zeropad>0)?
(?P<minimumwidth>(?!0)\d+)?
(?P<thousands_sep>,)?
(?:\.(?P<precision>0|(?!0)\d+))?
(?P<type>[a-zA-Z]{1,2})?
(?P<fractional>%\d?)?
\Z
""", re.VERBOSE)


def parseSpec(spec):
    m = formatSpecRe.match(spec)
    if m is None:
        raise ValueError("Invalid format specifier: " + spec)
    return m.groupdict()


def buildSpec(formatDict):
    spec = ""
    if formatDict["align"] is not None:
        if formatDict["fill"] is not None:
            spec += formatDict["fill"]
        spec += formatDict["align"]
    if formatDict["sign"] is not None:
        spec += formatDict["sign"]
    if formatDict["zeropad"] is not None:
        spec += formatDict["zeropad"]
    if formatDict["minimumwidth"] is not None:
        spec += formatDict["minimumwidth"]
    if formatDict["thousands_sep"] is not None:
        spec += formatDict["thousands_sep"]
    if formatDict["precision"] is not None:
        spec += "." + formatDict["precision"]
    if formatDict["type"] is not None:
        spec += formatDict["type"]
    if formatDict["fractional"] is not None:
        spec += formatDict["fractional"]
    return spec


def roundDecimal(d, accuracy = 0):
    places = decimal.Decimal("10") ** -accuracy
    return d.quantize(places)


def roundDecimalFraction(number, denominator):
    rounded = roundDecimal(number * decimal.Decimal(denominator)) / decimal.Decimal(denominator)
    return rounded


def splitFraction(value, denom=8):
    if denom not in [2, 4, 8]:
        raise ValueError("Bad denominator")
    fractionStrings = ["", "⅛", "¼", "⅜", "½", "⅝", "¾", "⅞"]

    negative = value < 0
    value = abs(value)
    roundednumber = roundDecimalFraction(value, denom)
    whole, part = divmod(roundednumber, 1)
    if negative:
        whole = -whole
    fraction = fractionStrings[int(part * len(fractionStrings))]
    return whole, fraction


def fixZeroes(d):
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fixZeroes(Decimal('1e3')) -> Decimal('100')
    fixZeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0


def randRangeLog(minval, maxval, precision=26):
    """Generate a logarithmically scaled random number"""
    minval = decimal.Decimal(minval)
    maxval = decimal.Decimal(maxval)
    prec = decimal.Decimal("10") ** precision

    # Swap values if provided in the wrong order
    if minval > maxval:
        minval, maxval = maxval, minval

    minlog = minval.log10()
    maxlog = maxval.log10()

    minintlog = (minlog * prec).to_integral_value()
    maxintlog = (maxlog * prec).to_integral_value()

    newintlog = decimal.Decimal(random.randint(minintlog, maxintlog))

    newlog = newintlog / precision

    newval = decimal.Decimal("10") ** newlog

    return newval
