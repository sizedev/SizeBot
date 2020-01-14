import decimal
import random
from sizebot.utils import parseSpec, buildSpec

__all__ = ["Decimal", "roundDecimal", "roundDecimalHalf", "fixZeroes", "toEighths", "randrangelog"]

Decimal = decimal.Decimal

# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


def roundDecimal(d, accuracy = 0):
    places = Decimal("10") ** -accuracy
    return d.quantize(places)


# Legacy support
def roundDecimalHalf(number):
    return roundDecimalFraction(number, 2)


def roundDecimalFraction(number, denominator):
    rounded = roundDecimal(number * Decimal(denominator)) / Decimal(denominator)
    return rounded


def toFraction(number, denom=8, spec=""):
    if denom not in [2, 4, 8]:
        raise ValueError("Bad denominator")
    parsedSpec = parseSpec(spec)
    parsedSpec["precision"] = None
    spec = buildSpec(parsedSpec)
    eighths = ["", "⅛", "¼", "⅜", "½", "⅝", "¾", "⅞"]
    roundednumber = roundDecimalFraction(number, denom)
    whole, part = divmod(roundednumber, 1)
    whole = format(fixZeroes(whole), spec)
    if whole == "0":
        if part == 0:
            return "0"
        if part < 0:
            whole = "-"
        else:
            whole = ""
    abspart = abs(part)
    numerator = abspart * len(eighths)
    return f"{whole}{eighths[int(numerator)]}"


def toEighths(number):
    return toFraction(number, 8)


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


def randrangelog(minval, maxval, precision=26):
    """Generate a logarithmically scaled random number"""
    minval = Decimal(minval)
    maxval = Decimal(maxval)
    prec = Decimal("10") ** precision

    # Swap values if provided in the wrong order
    if minval > maxval:
        minval, maxval = maxval, minval

    minlog = minval.log10()
    maxlog = maxval.log10()

    minintlog = (minlog * prec).to_integral_value()
    maxintlog = (maxlog * prec).to_integral_value()

    newintlog = Decimal(random.randint(minintlog, maxintlog))

    newlog = newintlog / precision

    newval = Decimal("10") ** newlog

    return newval
