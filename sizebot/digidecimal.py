import re
import decimal
import random

__all__ = ["Decimal", "roundDecimal", "fixZeroes", "randRangeLog", "DecimalSpec"]

# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


class Decimal(decimal.Decimal):
    def __format__(self, spec):
        value = fixZeroes(decimal.Decimal(self))
        dSpec = DecimalSpec.parse(spec)

        fraction = ""

        if Decimal("1e-10") < value < Decimal("1e10") or value == 0:
            dSpec.type = "f"
        else:
            dSpec.type = "e"

        if dSpec.type == "f" and dSpec.fractional:
            dSpec.precision = None
            try:
                denom = int(dSpec.fractional[1])
            except IndexError:
                denom = 8
            value, fraction = splitFraction(value, denom)

        if dSpec.precision is not None:
            precision = int(dSpec.precision)
            dSpec.precision = None
        else:
            precision = 2
        value = roundDecimal(value, precision)

        dSpec.fractional = None
        numspec = str(dSpec)
        formatted = format(value, numspec)

        if fraction:
            if formatted == "0":
                formatted = ""
            formatted += fraction
        return formatted


class DecimalSpec:
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

    def __init__(self, formatDict):
        self.align = formatDict["align"]
        self.fill = formatDict["fill"]
        self.sign = formatDict["sign"]
        self.zeropad = formatDict["zeropad"]
        self.minimumwidth = formatDict["minimumwidth"]
        self.thousands_sep = formatDict["thousands_sep"]
        self.precision = formatDict["precision"]
        self.type = formatDict["type"]
        self.fractional = formatDict["fractional"]

    @classmethod
    def parse(cls, spec):
        m = cls.formatSpecRe.match(spec)
        if m is None:
            raise ValueError("Invalid format specifier: " + spec)
        formatDict = m.groupdict()
        return cls(formatDict)

    def __str__(self):
        spec = ""
        if self.align is not None:
            if self.fill is not None:
                spec += self.fill
            spec += self.align
        if self.sign is not None:
            spec += self.sign
        if self.zeropad is not None:
            spec += self.zeropad
        if self.minimumwidth is not None:
            spec += self.minimumwidth
        if self.thousands_sep is not None:
            spec += self.thousands_sep
        if self.precision is not None:
            spec += "." + self.precision
        if self.type is not None:
            spec += self.type
        if self.fractional is not None:
            spec += self.fractional
        return spec


def roundDecimal(d, accuracy = 0):
    places = decimal.Decimal("10") ** -accuracy
    return fixZeroes(d.quantize(places))


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
    return fixZeroes(whole), fraction


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
