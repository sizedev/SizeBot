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
def _minmax(first: Decimal, second: Decimal) -> tuple[Decimal, Decimal]:
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
def _values(fn: Callable) -> Callable:
    def wrapped(*args) -> Any:
        valargs = [_unwrap_decimal(a) for a in args]
        return fn(*valargs)
    return wrapped


def _clamp_inf(value: RawDecimal, limit: RawDecimal) -> RawDecimal:
    if limit and abs(value) >= limit:
        value = RawDecimal("infinity") * int(math.copysign(1, value))
    return value


def _unwrap_decimal(value: Decimal) -> RawDecimal:
    if isinstance(value, Decimal):
        value = value._rawvalue
    return value


@total_ordering
class Decimal():
    infinity = RawDecimal("infinity")
    _infinity = RawDecimal("1e1000")

    def __init__(self, value: Decimal):
        # initialize from Decimal
        rawvalue = _unwrap_decimal(value)
        if isinstance(rawvalue, str):
            if rawvalue == "∞":
                rawvalue = "infinity"
            elif rawvalue == "-∞":
                rawvalue = "-infinity"
            # initialize from fraction string
            values = rawvalue.split("/")
            if len(values) == 2:
                numberator, denominator = values
                rawvalue = _unwrap_decimal(Decimal(numberator) / Decimal(denominator))
        self._rawvalue = _clamp_inf(RawDecimal(rawvalue), _unwrap_decimal(self._infinity))

    def __format__(self, spec: str) -> str:
        if self.is_infinite():
            return self.sign + "∞"

        value = self
        rounded = value

        d_spec = DecimalSpec.parse(spec)

        fractional = d_spec.fractional
        d_spec.fractional = None

        accuracy = d_spec.accuracy
        d_spec.accuracy = None

        precision = 2
        if d_spec.precision is not None:
            precision = int(d_spec.precision)

        if (Decimal("10") ** -(precision + 1)) < abs(value) < Decimal("1e10") or value == 0:
            d_spec.type = "f"
            d_spec.precision = None
            if fractional:
                try:
                    denom = int(fractional[1])
                except IndexError:
                    denom = 8
                rounded = round_fraction(value, denom)
            else:
                rounded = round(value, precision)
        else:
            d_spec.type = "e"
            d_spec.precision = str(precision)

        numspec = str(d_spec)
        if fractional:
            whole = rounded.to_integral_value(ROUND_DOWN)
            rawwhole = _fix_zeroes(whole._rawvalue)
            formatted = format(rawwhole, numspec)
            part = abs(whole - rounded)
            fraction = _format_fraction(part)
            if fraction:
                if formatted == "0":
                    formatted = ""
                formatted += fraction
        else:
            rawvalue = _fix_zeroes(rounded._rawvalue)
            formatted = format(rawvalue, numspec)

        if d_spec.type == "f":
            if accuracy:
                try:
                    roundamount = int(accuracy[1])
                except IndexError:
                    roundamount = 0
                small, big = _minmax(rounded, value)
                printacc = round((abs(small / big) * 100), roundamount)
                formatted += f" (~{printacc}% accurate)"

        return formatted

    def __str__(self) -> str:
        return str(self._rawvalue)

    def __repr__(self) -> str:
        return f"Decimal('{self}')"

    @_values
    def __bool__(value) -> bool:
        return bool(value)

    @_values
    def __hash__(value) -> int:
        return hash(value)

    # Math Methods
    @_values
    def __eq__(value, other: Any) -> bool:
        return value == other

    @_values
    def __lt__(value, other: Any) -> bool:
        return value < other

    @_values
    def __add__(value, other: Any) -> Decimal:
        return Decimal(value + other)

    def __radd__(self, other: Any) -> Decimal:
        return Decimal.__add__(other, self)

    @_values
    def __sub__(value, other: Any) -> Decimal:
        return Decimal(value - other)

    def __rsub__(self, other: Any) -> Decimal:
        return Decimal.__sub__(other, self)

    @_values
    def __mul__(value, other: Any) -> Decimal:
        return Decimal(value * other)

    def __rmul__(self, other: Any) -> Decimal:
        return Decimal.__mul__(other, self)

    @_values
    def __matmul__(value, other: Any) -> Decimal:
        return Decimal(value @ other)

    def __rmatmul__(self, other: Any) -> Decimal:
        return Decimal.__matmul__(other, self)

    @_values
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

    @_values
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

    @_values
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

    @_values
    def __pow__(value, other: Any) -> Decimal:
        return Decimal(value ** other)

    @_values
    def __rpow__(value, other: Any) -> Decimal:
        return Decimal(other ** value)

    @_values
    def __lshift__(value, other: Any) -> Decimal:
        return Decimal.__mul__(value, Decimal.__pow__(Decimal(2), other))

    def __rlshift__(self, other: Any) -> Decimal:
        return Decimal.__lshift__(other, self)

    @_values
    def __rshift__(value, other: Any) -> Decimal:
        return Decimal.__floordiv__(value, Decimal.__pow__(Decimal(2), other))

    def __rrshift__(self, other: Any) -> Decimal:
        return Decimal.__rshift__(other, self)

    @_values
    def __and__(value, other: Any) -> Decimal:
        if (isinstance(value, RawDecimal) and value.is_infinite()):
            return other
        elif (isinstance(other, RawDecimal) and other.is_infinite()):
            return value
        return Decimal(value & other)

    def __rand__(self, other: Any) -> Decimal:
        return Decimal.__and__(other, self)

    @_values
    def __xor__(value, other: Any) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return Decimal.__invert__(other)
        elif isinstance(other, RawDecimal) and other.is_infinite():
            return Decimal.__invert__(value)
        return Decimal(value ^ other)

    def __rxor__(self, other: Any) -> Decimal:
        return Decimal.__xor__(other, self)

    @_values
    def __or__(value, other: Any) -> Decimal:
        if (isinstance(value, RawDecimal) and value.is_infinite()) or (isinstance(other, RawDecimal) and other.is_infinite()):
            return Decimal("infinity")
        return Decimal(value | other)

    def __ror__(self, other: Any) -> Decimal:
        return Decimal.__or__(other, self)

    @_values
    def __neg__(value) -> Decimal:
        return Decimal(-value)

    @_values
    def __pos__(value) -> Decimal:
        return Decimal(+value)

    @_values
    def __abs__(value) -> Decimal:
        return Decimal(abs(value))

    @_values
    def __invert__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return -value
        return Decimal(~value)

    @_values
    def __complex__(value) -> complex:
        return complex(value)

    @_values
    def __int__(value) -> int:
        return int(value)

    @_values
    def __float__(value) -> float:
        return float(value)

    def __round__(value, ndigits: int = 0) -> Decimal:
        if value.is_infinite():
            return value
        exp = Decimal(10) ** -ndigits
        return value.quantize(exp)

    @_values
    def __trunc__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.trunc(value))

    @_values
    def __floor__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.floor(value))

    @_values
    def __ceil__(value) -> Decimal:
        if isinstance(value, RawDecimal) and value.is_infinite():
            return value
        return Decimal(math.ceil(value))

    @_values
    def quantize(value, exp: Decimal) -> Decimal:
        return Decimal(value.quantize(exp))

    @_values
    def is_infinite(value) -> bool:
        return value.is_infinite()

    @_values
    def is_signed(value) -> bool:
        return value.is_signed()

    @property
    @_values
    def sign(value) -> str:
        return "-" if value.is_signed() else ""

    def to_integral_value(self, *args, **kwargs) -> Decimal:
        return Decimal(self._rawvalue.to_integral_value(*args, **kwargs))

    @_values
    def log10(value) -> Decimal:
        return Decimal(value.log10())


class DecimalSpec:
    re_format_spec = re.compile(r"""\A
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

    def __init__(self, format_dict: dict[str, Any]):
        self.align = format_dict["align"]
        self.fill = format_dict["fill"]
        self.sign = format_dict["sign"]
        self.zeropad = format_dict["zeropad"]
        self.minimumwidth = format_dict["minimumwidth"]
        self.thousands_sep = format_dict["thousands_sep"]
        self.precision = format_dict["precision"]
        self.type = format_dict["type"]
        self.fractional = format_dict["fractional"]
        self.accuracy = format_dict["accuracy"]

    @classmethod
    def parse(cls, spec: str) -> DecimalSpec:
        m = cls.re_format_spec.match(spec)
        if m is None:
            raise ValueError("Invalid format specifier: " + spec)
        format_dict = m.groupdict()
        return cls(format_dict)

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


def _round_decimal(d: Decimal, accuracy: int = 0) -> Decimal:
    if d.is_infinite():
        return d
    places = Decimal(10) ** -accuracy
    return d.quantize(places)


def round_fraction(number: Decimal, denominator: Decimal) -> Decimal:
    rounded = round(number * denominator) / denominator
    return rounded


def _format_fraction(value: Decimal) -> str:
    if value is None:
        return None
    fraction_strings = ["", "⅛", "¼", "⅜", "½", "⅝", "¾", "⅞"]
    part = round_fraction(value % 1, 8)
    index = int(part * len(fraction_strings)) % len(fraction_strings)
    try:
        fraction = fraction_strings[index]
    except IndexError as e:
        logger.error("Weird fraction IndexError:\n"
                     f"fraction_strings = {fraction_strings!r}\n"
                     f"len(fraction_strings) = {len(fraction_strings)!r}\n"
                     f"value = {value._rawvalue}\n"
                     f"part = {part!r}\n"
                     f"int(part * len(fraction_strings)) = {int(part * len(fraction_strings))}")
        raise e
    return fraction


def _fix_zeroes(d: Decimal) -> Decimal:
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fixZeroes(Decimal('1e3')) -> Decimal('100')
    fixZeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0
