from __future__ import annotations
from abc import abstractmethod
from typing import Self, overload

import numbers
import decimal
import logging
import math
import re
from decimal import Decimal as RawDecimal, ROUND_DOWN
from functools import total_ordering

__all__ = ["BaseDecimal"]

logger = logging.getLogger("sizebot")

# local copy of utils.minmax to prevent circular import
def minmax[T: BaseDecimal](first: T, second: T) -> tuple[T, T]:
    """Return a tuple where item 0 is the smaller value, and item 1 is the larger value."""
    small, big = sorted((first, second))
    return small, big


# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.InvalidOperation])
decimal.setcontext(context)


@total_ordering
class BaseDecimal():
    infinity = RawDecimal("infinity")
    _infinity = RawDecimal("1e1000")

    def __init__(self, value: BaseDecimal | RawDecimal | float | int | str):
        self._rawvalue: RawDecimal
        if isinstance(value, RawDecimal):
            rawvalue = value
        elif isinstance(value, BaseDecimal):
            rawvalue = value._rawvalue
        elif isinstance(value, str):
            if value == "∞":
                value = "infinity"
            elif value == "-∞":
                value = "-infinity"
            # initialize from fraction string
            values = value.split("/")
            if len(values) == 2:
                numberator, denominator = values
                calcvalue = BaseDecimal(numberator) / BaseDecimal(denominator)
                rawvalue = calcvalue._rawvalue
            else:
                rawvalue = RawDecimal(value)
        else:
            rawvalue = RawDecimal(value)
        # initialize from Decimal
        if abs(rawvalue) >= self._infinity:
            rawvalue = RawDecimal("infinity") * int(math.copysign(1, rawvalue))
        self._rawvalue = rawvalue

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

        if (BaseDecimal("10") ** -(precision + 1)) < abs(value) < BaseDecimal("1e10") or value == 0:
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
            rawwhole = fix_zeroes(whole.to_pydecimal())
            formatted = format(rawwhole, numspec)
            part = abs(whole - rounded)
            fraction = format_fraction(part)
            if fraction:
                if formatted == "0":
                    formatted = ""
                formatted += fraction
        else:
            rawvalue = fix_zeroes(rounded.to_pydecimal())
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
        rawvalue = unwrap_decimal(self)
        return str(rawvalue)

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"

    def __bool__(self) -> bool:
        rawvalue = unwrap_decimal(self)
        return bool(rawvalue)

    def __hash__(self) -> int:
        rawvalue = unwrap_decimal(self)
        return hash(rawvalue)

    # Math Methods
    def __eq__(self, other: object) -> bool:
        rawvalue = unwrap_decimal(self)
        rawother = other.to_pydecimal() if isinstance(other, BaseDecimal) else other     # Don't use unwrap_decimal for object type
        return rawvalue == rawother

    def __lt__(self, other: BaseDecimal | float | int | numbers.Rational) -> bool:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return rawvalue < rawother

    @abstractmethod
    def __add__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawvalue + rawother)

    @abstractmethod
    def __radd__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawother + rawvalue)

    @abstractmethod
    def __sub__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        try:
            return BaseDecimal(rawvalue - rawother)
        except decimal.InvalidOperation as e:
            return BaseDecimal(0)

    @abstractmethod
    def __rsub__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawother - rawvalue)

    @abstractmethod
    def __mul__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawvalue * rawother)

    @abstractmethod
    def __rmul__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawother * rawvalue)

    @abstractmethod
    def __truediv__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if is_infinite(rawvalue) and is_infinite(rawother):
            raise decimal.InvalidOperation
        elif is_infinite(rawvalue):
            return BaseDecimal(rawvalue)
        elif is_infinite(rawother):
            return BaseDecimal(0)
        return BaseDecimal(rawvalue / rawother)

    @abstractmethod
    def __rtruediv__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if is_infinite(rawvalue) and is_infinite(rawother):
            raise decimal.InvalidOperation
        elif is_infinite(rawvalue):
            return BaseDecimal(0)
        elif is_infinite(rawother):
            return BaseDecimal(rawother)
        return BaseDecimal(rawother / rawvalue)

    @abstractmethod
    def __floordiv__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if is_infinite(rawvalue) and is_infinite(rawother):
            raise decimal.InvalidOperation
        elif is_infinite(rawvalue):
            return BaseDecimal(rawvalue)
        elif is_infinite(rawother):
            return BaseDecimal(0)
        return BaseDecimal(rawvalue // rawother)

    @abstractmethod
    def __rfloordiv__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if is_infinite(rawvalue) and is_infinite(rawother):
            raise decimal.InvalidOperation
        elif is_infinite(rawvalue):
            return BaseDecimal(0)
        elif is_infinite(rawother):
            return BaseDecimal(rawother)
        return BaseDecimal(rawother // rawvalue)

    @abstractmethod
    def __mod__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if is_infinite(rawvalue):
            return BaseDecimal(0)
        elif is_infinite(rawother):
            return BaseDecimal(rawother)
        return BaseDecimal(rawvalue % rawother)

    @abstractmethod
    def __rmod__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        if is_infinite(rawvalue):
            return BaseDecimal(rawother)
        elif is_infinite(rawother):
            return BaseDecimal(0)
        return BaseDecimal(rawother % rawvalue)

    @abstractmethod
    def __divmod__(self, other: BaseDecimal | int) -> tuple[BaseDecimal, BaseDecimal]:
        quotient = BaseDecimal.__floordiv__(self, other)
        remainder = BaseDecimal.__mod__(self, other)
        return quotient, remainder

    @abstractmethod
    def __rdivmod__(self, other: BaseDecimal | int) -> tuple[BaseDecimal, BaseDecimal]:
        quotient = BaseDecimal.__rfloordiv__(self, other)
        remainder = BaseDecimal.__rmod__(self, other)
        return quotient, remainder

    @abstractmethod
    def __pow__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawvalue ** rawother)

    @abstractmethod
    def __rpow__(self, other: BaseDecimal | int) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        rawother = unwrap_decimal(other)
        return BaseDecimal(rawother ** rawvalue)

    def __neg__(self) -> Self:
        rawvalue = unwrap_decimal(self)
        return type(self)(-rawvalue)

    def __pos__(self) -> Self:
        rawvalue = unwrap_decimal(self)
        return type(self)(+rawvalue)

    def __abs__(self) -> Self:
        rawvalue = unwrap_decimal(self)
        return type(self)(abs(rawvalue))

    def __complex__(self) -> complex:
        rawvalue = unwrap_decimal(self)
        return complex(rawvalue)

    def __int__(self) -> int:
        rawvalue = unwrap_decimal(self)
        return int(rawvalue)

    def __float__(self) -> float:
        rawvalue = unwrap_decimal(self)
        return float(rawvalue)

    def __round__(self, ndigits: int = 0) -> Self:
        rawvalue = unwrap_decimal(self)
        if rawvalue.is_infinite():
            return type(self)(rawvalue)
        exp = RawDecimal(10) ** -ndigits
        return type(self)(rawvalue.quantize(exp))

    def __trunc__(self) -> Self:
        rawvalue = unwrap_decimal(self)
        if rawvalue.is_infinite():
            return type(self)(rawvalue)
        return type(self)(math.trunc(rawvalue))

    def __floor__(self) -> Self:
        rawvalue = unwrap_decimal(self)
        if rawvalue.is_infinite():
            return type(self)(rawvalue)
        return type(self)(math.floor(rawvalue))

    def __ceil__(self) -> Self:
        rawvalue = unwrap_decimal(self)
        if rawvalue.is_infinite():
            return type(self)(rawvalue)
        return type(self)(math.ceil(rawvalue))

    def quantize(self, exp: BaseDecimal | int) -> Self:
        rawvalue = unwrap_decimal(self)
        rawexp = unwrap_decimal(exp)
        return type(self)(rawvalue.quantize(rawexp))

    def is_infinite(self) -> bool:
        rawvalue = unwrap_decimal(self)
        return rawvalue.is_infinite()

    def is_signed(self) -> bool:
        rawvalue = unwrap_decimal(self)
        return rawvalue.is_signed()

    @property
    def sign(self) -> str:
        rawvalue = unwrap_decimal(self)
        return "-" if rawvalue.is_signed() else ""

    def to_integral_value(self, rounding: str | None = None) -> Self:
        rawvalue = unwrap_decimal(self)
        return type(self)(rawvalue.to_integral_value(rounding))

    @abstractmethod
    def log10(self) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        return BaseDecimal(rawvalue.log10())

    @abstractmethod
    def sqrt(self) -> BaseDecimal:
        rawvalue = unwrap_decimal(self)
        return BaseDecimal(rawvalue.sqrt())

    def to_pydecimal(self) -> RawDecimal:
        return self._rawvalue


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

    def __init__(self, formatDict: dict[str, str|None]):
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


def round_decimal(d: BaseDecimal, accuracy: int = 0) -> BaseDecimal:
    if d.is_infinite():
        return d
    places = BaseDecimal(10) ** -accuracy
    return d.quantize(places)


def round_fraction(number: BaseDecimal, denominator: int) -> BaseDecimal:
    """
    Round to the nearest fractional amount
    round_fraction(1.8, 4) == 1.75
    """
    rounded = round(number * denominator) / denominator
    return rounded


def format_fraction(value: BaseDecimal) -> str:
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


def fix_zeroes(d: RawDecimal) -> RawDecimal:
    """Reset the precision of a Decimal to avoid values that use exponents like '1e3' and values with trailing zeroes like '100.000'

    fix_zeroes(Decimal('1e3')) -> Decimal('100')
    fix_zeroes(Decimal('100.000')) -> Decimal('100')

    Decimal.normalize() removes ALL trailing zeroes, including ones before the decimal place
    Decimal('100.000').normalize() -> Decimal('1e3')

    Added 0 adds enough precision to represent a zero, which means it re-adds the zeroes left of the decimal place, if necessary
    Decimal('1e3') -> Decimal('100')
    """
    return d.normalize() + 0


@overload
def unwrap_decimal(value: BaseDecimal) -> RawDecimal:
    ...

@overload
def unwrap_decimal(value: RawDecimal) -> RawDecimal:
    ...

@overload
def unwrap_decimal(value: int) -> int:
    ...

@overload
def unwrap_decimal(value: float) -> float:
    ...

@overload
def unwrap_decimal(value: numbers.Rational) -> numbers.Rational:
    ...

def unwrap_decimal(value: BaseDecimal | RawDecimal  | int | float | numbers.Rational) -> RawDecimal | int | float | numbers.Rational:
    if isinstance(value, BaseDecimal):
        value = value.to_pydecimal()
    return value

def is_infinite(value: RawDecimal | int):
    if not isinstance(value, RawDecimal):
        return False
    return value.is_infinite()

