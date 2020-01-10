import decimal
import random

__all__ = ["Decimal", "roundDecimal", "roundDecimalHalf", "trimZeroes", "toEighths", "randrangelog"]

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


def toFraction(number, denom=8):
    if denom not in [2, 4, 8]:
        raise ValueError("Bad denominator")

    eighths = ["", "⅛", "¼", "⅜", "½", "⅝", "¾", "⅞"]
    roundednumber = roundDecimalFraction(number, denom)
    whole, part = divmod(roundednumber, 1)
    whole = trimZeroes(whole)
    abspart = abs(part)
    numerator = abspart * len(eighths)
    return f"{whole}{eighths[int(numerator)]}"


def toEighths(number):
    return toFraction(number, 8)


def trimZeroes(d):
    """Remove any trailing zeroes after the decimal place from a Decimal"""
    # `normalize()` removes ALL trailing zeroes, including ones before the decimal place
    # `+ 0` re-adds the trailing zeroes before the decimal place, if necessary
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
