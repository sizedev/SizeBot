from __future__ import annotations
from typing import Any, TypeVar, overload
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
        valargs = [unwrap_decimal(a) for a in args]
        return fn(*valargs)
    return wrapped


def _clamp_inf(value: RawDecimal) -> RawDecimal:
    if abs(value) >= _max_num:
        value = RawDecimal("infinity") * int(math.copysign(1, value))
    return value


T = TypeVar("T", bound=RawDecimal | int | float | str)


@overload
def unwrap_decimal(value: Decimal) -> RawDecimal:
    ...


@overload
def unwrap_decimal(value: T) -> T:
    ...


def unwrap_decimal(value: Decimal | T) -> RawDecimal | T:
    if isinstance(value, Decimal):
        return value.to_pydecimal()
    return value


_max_num = RawDecimal("1e1000")


@total_ordering
class Decimal():
    infinity = RawDecimal("infinity")

    def __init__(self, value: Decimal | RawDecimal | int | float | str):
        # initialize from Decimal
        if isinstance(value, Decimal):
            rawvalue = value.to_pydecimal()
        elif isinstance(value, str):
            rawvalue = _parse_rawdecimal(value)
        elif isinstance(value, RawDecimal):
            rawvalue = value
        else:
            rawvalue = RawDecimal(value)
        self._rawvalue = _clamp_inf(rawvalue)

    def to_pydecimal(self) -> RawDecimal:
        return self._rawvalue

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
            rawwhole = _fix_zeroes(whole.to_pydecimal())
            formatted = format(rawwhole, numspec)
            part = abs(whole - rounded)
            fraction = format_fraction(part)
            if fraction:
                if formatted == "0":
                    formatted = ""
                formatted += fraction
        else:
            rawvalue = _fix_zeroes(rounded.to_pydecimal())
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
        return str(self.to_pydecimal())

    def __repr__(self) -> str:
        return f"Decimal('{self}')"

    def __bool__(self) -> bool:
        rawself = unwrap_decimal(self)
        return bool(rawself)

    def __hash__(self) -> int:
        rawself = unwrap_decimal(self)
        return hash(rawself)

    # Math Methods
    def __eq__(self, other: Decimal) -> bool:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return rawself == rawother

    def __lt__(self, other: Decimal) -> bool:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return rawself < rawother

    def __add__(self, other: Decimal) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawself + rawother)

    def __radd__(self, other: Decimal) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawother + rawself)

    def __sub__(self, other: Decimal) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawself - rawother)

    def __rsub__(self, other: Decimal) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawother - rawself)

    def __mul__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawself * rawother)

    def __rmul__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawother * rawself)

    def __truediv__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if rawself.is_infinite() and _is_infinite(rawother):
            raise decimal.InvalidOperation
        elif rawself.is_infinite():
            return Decimal(rawself)
        elif _is_infinite(rawother):
            return Decimal(0)
        return Decimal(rawself / rawother)

    def __rtruediv__(self, other: Decimal) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if rawself.is_infinite() and rawother.is_infinite():
            raise decimal.InvalidOperation
        elif rawself.is_infinite():
            return Decimal(0)
        elif rawother.is_infinite():
            return Decimal(rawself)
        return Decimal(rawother / rawself)

    def __floordiv__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if rawself.is_infinite() and _is_infinite(rawother):
            raise decimal.InvalidOperation
        elif rawself.is_infinite():
            return Decimal(rawself)
        elif _is_infinite(rawother):
            return Decimal(0)
        return Decimal(rawself // rawother)

    def __rfloordiv__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if rawself.is_infinite() and _is_infinite(rawother):
            raise decimal.InvalidOperation
        elif rawself.is_infinite():
            return Decimal(0)
        elif _is_infinite(rawother):
            return Decimal(rawself)
        return Decimal(rawother // rawself)

    def __mod__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if rawself.is_infinite():
            return Decimal(0)
        elif _is_infinite(rawother):
            return Decimal(rawself)
        return Decimal(rawself % rawother)

    def __rmod__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if rawself.is_infinite():
            return Decimal(rawself)
        elif _is_infinite(rawother):
            return Decimal(0)
        return Decimal(rawother % rawself)

    def __divmod__(self, other: Decimal | int) -> tuple[Decimal, Decimal]:
        quotient = Decimal.__floordiv__(self, other)
        remainder = Decimal.__mod__(self, other)
        return quotient, remainder

    def __rdivmod__(self, other: Decimal | int) -> tuple[Decimal, Decimal]:
        quotient = Decimal.__rfloordiv__(self, other)
        remainder = Decimal.__rmod__(self, other)
        return quotient, remainder

    def __pow__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawself ** rawother)

    def __rpow__(self, other: Decimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return Decimal(rawother ** rawself)

    def __neg__(self) -> Decimal:
        rawself = unwrap_decimal(self)
        return Decimal(-rawself)

    def __pos__(self) -> Decimal:
        rawself = unwrap_decimal(self)
        return Decimal(+rawself)

    def __abs__(self) -> Decimal:
        rawself = unwrap_decimal(self)
        return Decimal(abs(rawself))

    def __complex__(self) -> complex:
        rawself = unwrap_decimal(self)
        return complex(rawself)

    def __int__(self) -> int:
        rawself = unwrap_decimal(self)
        return int(rawself)

    def __float__(self) -> float:
        rawself = unwrap_decimal(self)
        return float(rawself)

    def __round__(self, ndigits: int = 0) -> Decimal:
        rawself = unwrap_decimal(self)
        if rawself.is_infinite():
            return Decimal(rawself)
        exp = RawDecimal(10) ** -ndigits
        return Decimal(rawself.quantize(exp))

    def __trunc__(self) -> Decimal:
        rawself = unwrap_decimal(self)
        if rawself.is_infinite():
            return Decimal(rawself)
        return Decimal(math.trunc(rawself))

    def __floor__(self) -> Decimal:
        rawself = unwrap_decimal(self)
        if rawself.is_infinite():
            return Decimal(rawself)
        return Decimal(math.floor(rawself))

    def __ceil__(self) -> Decimal:
        rawself = unwrap_decimal(self)
        if rawself.is_infinite():
            return Decimal(rawself)
        return Decimal(math.ceil(rawself))

    def quantize(self, exp: Decimal | RawDecimal | int) -> Decimal:
        rawself = unwrap_decimal(self)
        rawexp = unwrap_decimal(exp)
        return Decimal(rawself.quantize(rawexp))

    def is_infinite(self) -> bool:
        rawself = unwrap_decimal(self)
        return rawself.is_infinite()

    def is_signed(self) -> bool:
        rawself = unwrap_decimal(self)
        return rawself.is_signed()

    @property
    def sign(self) -> str:
        rawself = unwrap_decimal(self)
        return "-" if rawself.is_signed() else ""

    def to_integral_value(self, rounding: str | None = None) -> Decimal:
        rawself = unwrap_decimal(self)
        return Decimal(rawself.to_integral_value(rounding))

    def log10(self) -> Decimal:
        rawself = unwrap_decimal(self)
        return Decimal(rawself.log10())


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


def round_fraction(number: Decimal, denominator: int) -> Decimal:
    rounded = round(number * denominator) / denominator
    return rounded


def format_fraction(value: Decimal) -> str | None:
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
                     f"value = {value.to_pydecimal()}\n"
                     f"part = {part!r}\n"
                     f"int(part * len(fractionStrings)) = {int(part * len(fractionStrings))}")
        raise e
    return fraction


def _fix_zeroes(d: RawDecimal) -> RawDecimal:
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fixZeroes(Decimal('1e3')) -> Decimal('100')
    fixZeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0


def _parse_rawdecimal(s: str) -> RawDecimal:
    if s == "∞":
        s = "infinity"
    elif s == "-∞":
        s = "-infinity"
    # initialize from fraction string
    parts = s.split("/")
    if len(parts) == 2:
        numberator, denominator = parts
        value = Decimal(numberator) / Decimal(denominator)
        value.to_pydecimal()
    return RawDecimal(s)


def _is_infinite(d: RawDecimal | int) -> bool:
    if isinstance(d, RawDecimal):
        return d.is_infinite()
    return False
