# TODO: Shouldn't this be in the lib folder?

import math
import re
import decimal
from decimal import Decimal as RawDecimal
import random
from functools import total_ordering

__all__ = ["Decimal", "randRangeLog", "DecimalSpec"]

# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.InvalidOperation])
decimal.setcontext(context)


# get the values for magic methods, instead of the objects
def values(fn):
    def wrapped(*args):
        valargs = [unwrapDecimal(a) for a in args]
        return fn(*valargs)
    return wrapped


def clampInf(value, limit):
    if limit and abs(value) >= limit:
        value = RawDecimal("infinity") * int(math.copysign(1, value))
    return value


def unwrapDecimal(value):
    if isinstance(value, Decimal):
        value = value.value
    return value


@total_ordering
class Decimal():
    infinity = RawDecimal("infinity")
    _infinity = RawDecimal("1e100")

    def __init__(self, value):
        # initialize from Decimal
        rawvalue = unwrapDecimal(value)
        if isinstance(rawvalue, str):
            if rawvalue == "∞":
                rawvalue = "infinity"
            elif rawvalue == "-∞":
                rawvalue = "-infinity"
            # initialize from fraction string
            values = rawvalue.split("/")
            if len(values) == 2:
                numberator, denominator = values
                rawvalue = unwrapDecimal(Decimal(numberator) / Decimal(denominator))
        self.value = clampInf(RawDecimal(rawvalue), unwrapDecimal(self._infinity))

    def __format__(self, spec):
        if self.is_infinite():
            return self.sign + "∞"

        value = self
        dSpec = DecimalSpec.parse(spec)

        fraction = ""

        if Decimal("1e-10") < value < Decimal("1e10") or value == 0:
            dSpec.type = "f"
            if dSpec.fractional:
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
            value = round(value, precision)
        else:
            dSpec.type = "e"
            if dSpec.precision is None:
                dSpec.precision = 2

        dSpec.fractional = None
        numspec = str(dSpec)
        rawvalue = fixZeroes(RawDecimal(value.value))
        formatted = format(rawvalue, numspec)

        if fraction:
            if formatted == "0":
                formatted = ""
            formatted += fraction
        return formatted

    def __str__(self):
        return format(self)

    def __repr__(self):
        return f"Decimal('{self}')"

    def __bool__(self):
        return bool(self.value)

    @values
    def __hash__(value):
        raise hash(value)

    # Math Methods
    @values
    def __eq__(value, other):
        return value == other

    @values
    def __lt__(value, other):
        return value < other

    @values
    def __add__(value, other):
        return Decimal(value + other)

    def __radd__(self, other):
        return Decimal.__add__(other, self)

    @values
    def __sub__(value, other):
        return Decimal(value - other)

    def __rsub__(self, other):
        return Decimal.__sub__(other, self)

    @values
    def __mul__(value, other):
        return Decimal(value * other)

    def __rmul__(self, other):
        return Decimal.__mul__(other, self)

    @values
    def __matmul__(value, other):
        return Decimal(value @ other)

    def __rmatmul__(self, other):
        return Decimal.__matmul__(other, self)

    @values
    def __truediv__(value, other):
        if isinstance(value, RawDecimal) and value.is_infinite() and isinstance(other, RawDecimal) and other.is_infinite():
            raise RawDecimal.InvalidOperation
        elif isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal(value)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal(0)
        return Decimal(value / other)

    def __rtruediv__(self, other):
        return Decimal.__truediv__(other, self)

    @values
    def __floordiv__(value, other):
        if isinstance(value, RawDecimal) and value.is_infinite() and isinstance(other, RawDecimal) and other.is_infinite():
            raise RawDecimal.InvalidOperation
        elif isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal(value)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal(0)
        return Decimal(value // other)

    def __rfloordiv__(self, other):
        return Decimal.__floordiv__(other, self)

    @values
    def __mod__(value, other):
        if isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal(0)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal(value)
        return Decimal(value % other)

    def __rmod__(self, other):
        return Decimal.__mod__(other, self)

    def __divmod__(self, other):
        quotient = Decimal.__floordiv__(self, other)
        remainder = Decimal.__mod__(self, other)
        return Decimal(quotient), Decimal(remainder)

    def __rdivmod__(self, other):
        return Decimal.__divmod__(other, self)

    @values
    def __pow__(value, other):
        return Decimal(value ** other)

    @values
    def __rpow__(value, other):
        return Decimal(other ** value)

    @values
    def __lshift__(value, other):
        return Decimal.__mul__(value, Decimal.__pow__(Decimal(2), other))

    def __rlshift__(self, other):
        return Decimal.__lshift__(other, self)

    @values
    def __rshift__(value, other):
        return Decimal.__floordiv__(value, Decimal.__pow__(Decimal(2), other))

    def __rrshift__(self, other):
        return Decimal.__rshift__(other, self)

    @values
    def __and__(value, other):
        if (isinstance(value, RawDecimal) and value.is_infinite()):
            return other
        elif (isinstance(other, RawDecimal) and other.is_infinite()):
            return value
        return Decimal(value & other)

    def __rand__(self, other):
        return Decimal.__and__(other, self)

    @values
    def __xor__(value, other):
        if isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal.__invert__(other)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal.__invert__(value)
        return Decimal(value ^ other)

    def __rxor__(self, other):
        return Decimal.__xor__(other, self)

    @values
    def __or__(value, other):
        if (isinstance(value, RawDecimal) and value.is_infinite()) or (isinstance(other, RawDecimal) and other.is_infinite()):
            return Decimal("infinity")
        return Decimal(value | other)

    def __ror__(self, other):
        return Decimal.__or__(other, self)

    @values
    def __neg__(value):
        return Decimal(-value)

    @values
    def __pos__(value):
        return Decimal(+value)

    @values
    def __abs__(value):
        return Decimal(abs(value))

    @values
    def __invert__(value):
        if isinstance(value, RawDecimal) and value.is_infinite():
            return -value
        return Decimal(~value)

    @values
    def __complex__(value):
        return complex(value)

    @values
    def __int__(value):
        return int(value)

    @values
    def __float__(value):
        return float(value)

    def __round__(value, ndigits=0):
        if value.is_infinite():
            return value
        exp = Decimal(10) ** -ndigits
        return value.quantize(exp)

    @values
    def __trunc__(value):
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.trunc(value))

    @values
    def __floor__(value):
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.floor(value))

    @values
    def __ceil__(value):
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.ceil(value))

    @values
    def quantize(value, exp):
        return Decimal(value.quantize(exp))

    @values
    def is_infinite(value):
        return value.is_infinite()

    @values
    def is_signed(value):
        return value.is_signed()

    @property
    @values
    def sign(value):
        return "-" if value.is_signed() else ""


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
            spec += "." + str(self.precision)
        if self.type is not None:
            spec += self.type
        if self.fractional is not None:
            spec += self.fractional
        return spec


def roundDecimal(d, accuracy = 0):
    if d.is_infinite():
        return d
    places = Decimal(10) ** -accuracy
    return d.quantize(places)


def roundFraction(number, denominator):
    rounded = round(number * denominator) / denominator
    return rounded


def splitFraction(value, denom=8):
    if denom not in [2, 4, 8]:
        raise ValueError("Bad denominator")

    fractionStrings = ["", "⅛", "¼", "⅜", "½", "⅝", "¾", "⅞"]

    negative = value < 0
    value = abs(value)
    roundednumber = roundFraction(value, denom)
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
    """Generate a logarithmically scaled random number."""
    minval = Decimal(minval)
    maxval = Decimal(maxval)
    prec = Decimal(10) ** precision

    # Swap values if provided in the wrong order.
    if minval > maxval:
        minval, maxval = maxval, minval

    minlog = minval.log10()
    maxlog = maxval.log10()

    minintlog = (minlog * prec).to_integral_value()
    maxintlog = (maxlog * prec).to_integral_value()

    newintlog = Decimal(random.randint(minintlog, maxintlog))

    newlog = newintlog / precision

    newval = 10 ** newlog

    return newval
