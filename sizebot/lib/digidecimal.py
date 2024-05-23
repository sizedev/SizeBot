from __future__ import annotations
from typing import Any
from collections.abc import Callable

import decimal
import logging
import math
import re
from decimal import Decimal as RawDecimal
from decimal import ROUND_DOWN
from functools import total_ordering

__all__ = ["Decimal"]

logger = logging.getLogger("sizebot")


# local copy of utils.minmax to prevent circular import
def minmax(first: Decimal, second: Decimal) -> tuple[Decimal, Decimal]:
    """Return a tuple where item 0 is the smaller value, and item 1 is the larger value."""
    small, big = first, second
    if small > big:
        small, big = big, small
    return small, big


# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.InvalidOperation])
decimal.setcontext(context)


# get the values for magic methods, instead of the objects
def values(fn: Callable) -> Callable:
    def wrapped(*args) -> Any:
        valargs = [unwrapDecimal(a) for a in args]
        return fn(*valargs)
    return wrapped


# TODO: CamelCase
def clampInf(value: RawDecimal, limit: RawDecimal) -> RawDecimal:
    if limit and abs(value) >= limit:
        value = RawDecimal("infinity") * int(math.copysign(1, value))
    return value


# TODO: CamelCase
def unwrapDecimal(value: Decimal) -> RawDecimal:
    if isinstance(value, Decimal):
        value = value._rawvalue
    return value


@total_ordering
class Decimal():
    infinity = RawDecimal("infinity")
    _infinity = RawDecimal("1e1000")

    def __init__(self, value: Decimal | str | int | float):
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
        self._rawvalue = clampInf(RawDecimal(rawvalue), unwrapDecimal(self._infinity))

    def __format__(self, spec: str) -> str:
        if self.is_infinite():
            return self.sign + "∞"

        value = self
        rounded = value

        dSpec = DecimalSpec.parse(spec)

        fractional = dSpec.fractional
        dSpec.fractional = None

        accuracy = dSpec.accuracy
        dSpec.accuracy = None

        precision = 2
        if dSpec.precision is not None:
            precision = int(dSpec.precision)

        if (Decimal("10") ** -(precision + 1)) < abs(value) < Decimal("1e10") or value == 0:
            dSpec.type = "f"
            dSpec.precision = None
            if fractional:
                try:
                    denom = int(fractional[1])
                except IndexError:
                    denom = 8
                rounded = round_fraction(value, denom)
            else:
                rounded = round(value, precision)
        else:
            dSpec.type = "e"
            dSpec.precision = str(precision)

        numspec = str(dSpec)
        if fractional:
            whole = rounded.to_integral_value(ROUND_DOWN)
            rawwhole = fix_zeroes(whole._rawvalue)
            formatted = format(rawwhole, numspec)
            part = abs(whole - rounded)
            fraction = format_fraction(part)
            if fraction:
                if formatted == "0":
                    formatted = ""
                formatted += fraction
        else:
            rawvalue = fix_zeroes(rounded._rawvalue)
            formatted = format(rawvalue, numspec)

        if dSpec.type == "f":
            if accuracy:
                try:
                    roundamount = int(accuracy[1])
                except IndexError:
                    roundamount = 0
                small, big = minmax(rounded, value)
                printacc = round((abs(small / big) * 100), roundamount)
                formatted += f" (~{printacc}% accurate)"

        return formatted

    def __str__(self) -> str:
        return str(self._rawvalue)

    def __repr__(self) -> str:
        return f"Decimal('{self}')"

    @values
    def __bool__(value) -> bool:
        return bool(value)

    @values
    def __hash__(value) -> int:
        return hash(value)

    # Math Methods
    @values
    def __eq__(value, other: Any) -> bool:
        return value == other

    @values
    def __lt__(value, other: Any) -> bool:
        return value < other

    @values
    def __add__(value, other: Any) -> Decimal:
        return Decimal(value + other)

    def __radd__(self, other: Any) -> Decimal:
        return Decimal.__add__(other, self)

    @values
    def __sub__(value, other: Any) -> Decimal:
        return Decimal(value - other)

    def __rsub__(self, other: Any) -> Decimal:
        return Decimal.__sub__(other, self)

    @values
    def __mul__(value, other: Any) -> Decimal:
        return Decimal(value * other)

    def __rmul__(self, other: Any) -> Decimal:
        return Decimal.__mul__(other, self)

    @values
    def __matmul__(value, other: Any) -> Decimal:
        return Decimal(value @ other)

    def __rmatmul__(self, other: Any) -> Decimal:
        return Decimal.__matmul__(other, self)

    @values
    def __truediv__(value, other: Any) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite() and isinstance(other, RawDecimal) and other.is_infinite():
            raise decimal.InvalidOperation
        elif isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal(value)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal(0)
        return Decimal(value / other)

    def __rtruediv__(self, other: Any) -> Decimal:
        return Decimal.__truediv__(other, self)

    @values
    def __floordiv__(value, other: Any) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite() and isinstance(other, RawDecimal) and other.is_infinite():
            raise decimal.InvalidOperation
        elif isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal(value)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal(0)
        return Decimal(value // other)

    def __rfloordiv__(self, other: Any) -> Decimal:
        return Decimal.__floordiv__(other, self)

    @values
    def __mod__(value, other: Any) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal(0)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal(value)
        return Decimal(value % other)

    def __rmod__(self, other: Any) -> Decimal:
        return Decimal.__mod__(other, self)

    def __divmod__(self, other: Any) -> tuple[Decimal, Decimal]:
        quotient = Decimal.__floordiv__(self, other)
        remainder = Decimal.__mod__(self, other)
        return Decimal(quotient), Decimal(remainder)

    def __rdivmod__(self, other: Any) -> tuple[Decimal, Decimal]:
        return Decimal.__divmod__(other, self)

    @values
    def __pow__(value, other: Any) -> Decimal:
        return Decimal(value ** other)

    @values
    def __rpow__(value, other: Any) -> Decimal:
        return Decimal(other ** value)

    @values
    def __lshift__(value, other: Any) -> Decimal:
        return Decimal.__mul__(value, Decimal.__pow__(Decimal(2), other))

    def __rlshift__(self, other: Any) -> Decimal:
        return Decimal.__lshift__(other, self)

    @values
    def __rshift__(value, other: Any) -> Decimal:
        return Decimal.__floordiv__(value, Decimal.__pow__(Decimal(2), other))

    def __rrshift__(self, other: Any) -> Decimal:
        return Decimal.__rshift__(other, self)

    @values
    def __and__(value, other: Any) -> Decimal:
        if (isinstance(value, RawDecimal) and value.is_infinite()):
            return other
        elif (isinstance(other, RawDecimal) and other.is_infinite()):
            return value
        return Decimal(value & other)

    def __rand__(self, other: Any) -> Decimal:
        return Decimal.__and__(other, self)

    @values
    def __xor__(value, other: Any) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal.__invert__(other)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal.__invert__(value)
        return Decimal(value ^ other)

    def __rxor__(self, other: Any) -> Decimal:
        return Decimal.__xor__(other, self)

    @values
    def __or__(value, other: Any) -> Decimal:
        if (isinstance(value, RawDecimal) and value.is_infinite()) or (isinstance(other, RawDecimal) and other.is_infinite()):
            return Decimal("infinity")
        return Decimal(value | other)

    def __ror__(self, other: Any) -> Decimal:
        return Decimal.__or__(other, self)

    @values
    def __neg__(value) -> Decimal:
        return Decimal(-value)

    @values
    def __pos__(value) -> Decimal:
        return Decimal(+value)

    @values
    def __abs__(value) -> Decimal:
        return Decimal(abs(value))

    @values
    def __invert__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return -value
        return Decimal(~value)

    @values
    def __complex__(value) -> complex:
        return complex(value)

    @values
    def __int__(value) -> int:
        return int(value)

    @values
    def __float__(value) -> float:
        return float(value)

    def __round__(value, ndigits: int = 0) -> Decimal:
        if value.is_infinite():
            return value
        exp = Decimal(10) ** -ndigits
        return value.quantize(exp)

    @values
    def __trunc__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.trunc(value))

    @values
    def __floor__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.floor(value))

    @values
    def __ceil__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.ceil(value))

    @values
    def quantize(value, exp: Decimal) -> Decimal:
        return Decimal(value.quantize(exp))

    @values
    def is_infinite(value) -> bool:
        return value.is_infinite()

    @values
    def is_signed(value) -> bool:
        return value.is_signed()

    @property
    @values
    def sign(value) -> str:
        return "-" if value.is_signed() else ""

    def to_integral_value(self, *args, **kwargs) -> Decimal:
        return Decimal(self._rawvalue.to_integral_value(*args, **kwargs))

    @values
    def log10(value) -> Decimal:
        return Decimal(value.log10())


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
    (?P<accuracy>&\d?)?
    \Z
    """, re.VERBOSE)

    def __init__(self, formatDict: dict[str, Any]):
        self.align = formatDict["align"]
        self.fill = formatDict["fill"]
        self.sign = formatDict["sign"]
        self.zeropad = formatDict["zeropad"]
        self.minimumwidth = formatDict["minimumwidth"]
        self.thousands_sep = formatDict["thousands_sep"]
        self.precision = formatDict["precision"]
        self.type = formatDict["type"]
        self.fractional = formatDict["fractional"]
        self.accuracy = formatDict["accuracy"]

    @classmethod
    def parse(cls, spec: str) -> DecimalSpec:
        m = cls.formatSpecRe.match(spec)
        if m is None:
            raise ValueError("Invalid format specifier: " + spec)
        formatDict = m.groupdict()
        return cls(formatDict)

    def __str__(self) -> str:
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
        if self.accuracy is not None:
            spec += self.accuracy
        return spec


def round_decimal(d: Decimal, accuracy: int = 0) -> Decimal:
    if d.is_infinite():
        return d
    places = Decimal(10) ** -accuracy
    return d.quantize(places)


def round_fraction(number: Decimal, denominator: Decimal) -> Decimal:
    rounded = round(number * denominator) / denominator
    return rounded


def format_fraction(value: Decimal) -> str:
    if value is None:
        return None
    fractionStrings = ["", "⅛", "¼", "⅜", "½", "⅝", "¾", "⅞"]
    part = round_fraction(value % 1, 8)
    index = int(part * len(fractionStrings)) % len(fractionStrings)
    try:
        fraction = fractionStrings[index]
    except IndexError as e:
        logger.error("Weird fraction IndexError:\n"
                     f"fractionStrings = {fractionStrings!r}\n"
                     f"len(fractionStrings) = {len(fractionStrings)!r}\n"
                     f"value = {value._rawvalue}\n"
                     f"part = {part!r}\n"
                     f"int(part * len(fractionStrings)) = {int(part * len(fractionStrings))}")
        raise e
    return fraction


def fix_zeroes(d: Decimal) -> Decimal:
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fixZeroes(Decimal('1e3')) -> Decimal('100')
    fixZeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0
