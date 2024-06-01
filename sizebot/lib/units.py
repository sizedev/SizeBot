# pyright: reportIncompatibleMethodOverride=false, reportUnnecessaryIsInstance=false

from __future__ import annotations
from bisect import insort
from typing import Any, Literal, Never, NotRequired, Type, TypedDict, TypeVar, overload, override
from collections.abc import Iterator, Mapping

import importlib.resources as pkg_resources
import json
import logging
import re
from functools import total_ordering

from sizebot.lib.loglevels import EGG
import sizebot.data
import sizebot.data.units
from sizebot.lib import errors
from sizebot.lib.digidecimal import BaseDecimal, DecimalSpec, RawDecimal
from sizebot.lib.types import BotContext


__all__ = ["Mult", "SV", "WV", "TV", "AV", "VV"]

logger = logging.getLogger("sizebot")


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
(?P<fractional>%)?
\Z
""", re.VERBOSE)
re_num = r"\d+\.?\d*"

def remove_brackets(s: str) -> str:
    """Remove all [] and <>s from a string."""
    s = re.sub(r"[\[\]<>]", "", s)
    return s

class Mult():
    """Mult"""
    multPrefixes = ["x", "X", "*", "times", "mult", "multiply"]
    divPrefixes = ["/", "÷", "div", "divide"]
    prefixes = '|'.join(re.escape(p) for p in multPrefixes + divPrefixes)
    suffixes = '|'.join(re.escape(p) for p in ["x", "X", "%"])
    re_mult = re.compile(f"(?P<prefix>{prefixes})? *(?P<multValue>{re_num}) *(?P<suffix>{suffixes})?")

    @classmethod
    def parse(cls, s: str) -> Decimal:
        match = cls.re_mult.match(s)
        if match is None:
            raise errors.InvalidSizeValue(s, "multiplier")
        prefix = match.group("prefix") or match.group("suffix")
        multValue = Decimal(match.group("multValue"))

        isDivide = prefix in cls.divPrefixes
        if isDivide:
            multValue = 1 / multValue
        if prefix == "%":
            multValue = multValue / 100

        return multValue

class UnitJson(TypedDict):
    factor: str
    symbol: NotRequired[str]
    name: NotRequired[str]
    namePlural: NotRequired[str]
    names: NotRequired[list[str]]
    symbols: NotRequired[list[str]]
    fractional: NotRequired[bool]

class SystemJson(TypedDict):
    unit: str
    trigger: NotRequired[str]
    rel_trigger: NotRequired[str]

class UnitSystemJson(TypedDict):
    units: list[UnitJson]
    systems: dict[str, list[SystemJson]]

@total_ordering
class Unit():
    """Formats a value by scaling it and applying the appropriate symbol suffix"""

    def __init__(
        self,
        factor: Decimal,
        symbol: str | tuple[str, ...] | None,
        name: str | None,
        namePlural: str | None,
        symbols: list[str] | None = None,
        names: list[str] | None = None,
        fractional: bool = False,
        hidden: bool = False
    ):
        self.factor = factor
        self.symbol = symbol
        self.name = name
        self.namePlural = namePlural
        self.symbols: set[str | tuple[str, ...]] = set(symbols or [])  # case sensitive symbols
        if symbol is not None:
            self.symbols.add(symbol)
        self.names = set(n.lower() for n in (names or []))  # case insensitive names
        if name is not None:
            self.names.add(name.lower())
        if namePlural is not None:
            self.names.add(namePlural.lower())
        self.fractional = fractional
        self.hidden = hidden

    def format(self, value: Decimal, spec: str = "", preferName: bool = False) -> str:
        if value.is_infinite():
            if preferName:
                return value.sign + "infinity"
            else:
                return value.sign + "∞"
        scaled = value / self.factor
        if not self.fractional:
            dSpec = DecimalSpec.parse(spec)
            dSpec.fractional = None
            spec = str(dSpec)
        formattedValue = format(scaled, spec)

        if formattedValue == "0":
            return formattedValue

        single = formattedValue in ["-1", "1"]
        if single:
            name = self.name or self.namePlural
        else:
            name = self.namePlural or self.name

        if preferName:
            if name is not None:
                formatted = f"{formattedValue} {name}"
            elif self.symbol is not None:
                formatted = f"{formattedValue}{self.symbol}"
            else:
                formatted = formattedValue
        else:
            if self.symbol is not None:
                formatted = f"{formattedValue}{self.symbol}"
            elif name is not None:
                formatted = f"{formattedValue} {name}"
            else:
                formatted = formattedValue

        return formatted

    def to_base_unit(self, v: Decimal) -> Decimal:
        return v * self.factor

    def is_unit(self, u: str | tuple[str, ...]) -> bool:
        if not isinstance(u, str):
            return False
        u = u.strip()
        return u.lower() in self.names or u in self.symbols

    @property
    def id(self) -> str | tuple[str, ...]:
        return self.symbol or self.name or self.namePlural

    def __str__(self) -> str:
        if self.name is not None and self.symbol is not None:
            return f"{self.name.strip()} ({self.symbol.strip()})"
        if self.name is not None:
            return self.name.strip()
        if self.symbol is not None:
            return self.symbol.strip()
        return "?"

    def __lt__(self, other: SystemUnit) -> bool:
        return self.factor < other.factor

    def __eq__(self, other: SystemUnit) -> bool:
        return self.factor == other.factor

    @classmethod
    def from_json(cls, json: UnitJson) -> Unit:
        factor = Decimal(json["factor"])
        symbol = json.get("symbol")
        name = json.get("name")
        namePlural = json.get("namePlural")
        symbols = json.get("symbols", [])  # case sensitive symbols
        names = json.get("names", [])  # case insensitive names
        fractional = json.get("fractional", False)
        return Unit(factor, symbol, name, namePlural, symbols, names, fractional)


class FixedUnit(Unit):
    """Unit that only formats to a single symbol"""

    def format(self, value: Decimal, spec: str = "", preferName: bool = False) -> str:
        return self.symbol

    def to_base_unit(self, v: Decimal) -> Decimal:
        return self.factor


class FeetAndInchesUnit(Unit):
    """Unit for handling feet and inches"""

    def __init__(self):
        foot = INCH * 12
        super().__init__(
            factor=foot,
            symbol=("'", "\""),
            name=None,
            namePlural=None,
            symbols=[],
            names=[],
            fractional=False,
            hidden = True
        )

    def format(self, value: Decimal, spec: str = "", preferName: bool = False) -> str:
        feetSpec = DecimalSpec.parse(spec)
        feetSpec.precision = "0"

        inchSpec = DecimalSpec.parse(spec)
        inchSpec.sign = None

        inchval = value / INCH             # convert to inches
        precision = 2
        if inchSpec.precision is not None:
            precision = int(inchSpec.precision)
        inchval = round(inchval, precision)

        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches
        if inchval < Decimal("1e-100"):
            inchval = Decimal("0")

        formatted = f"{feetval:{feetSpec}}'{inchval:{inchSpec}}\""
        return formatted

    def to_base_unit(self, v: Decimal) -> None:
        return None

    def is_unit(self, u: str) -> bool:
        return u == self.symbol


class UnitRegistry(Mapping[str | tuple[str, ...], Unit]):
    """Unit Registry"""

    def __init__(self):
        self._units: list[Unit] = []
        self._symbol_map: dict[str | tuple[str, ...], Unit] = {}
        self._name_map: dict[str, Unit] = {}

    def __getitem__(self, key: str | tuple[str, ...]) -> Unit:
        if key in self._symbol_map:
            return self._symbol_map[key]
        if isinstance(key, str) and key.lower() in self._name_map:
            return self._name_map[key.lower()]
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        if key in self._symbol_map:
            return True
        if isinstance(key, str) and key.lower() in self._name_map:
            return True
        return False

    def __iter__(self) -> Iterator[Unit]:
        return iter(self._units)

    def __len__(self) -> int:
        return len(self._units)

    def add_unit(self, unit: Unit):
        if not unit.hidden:
            self._units.append(unit)
        for s in unit.symbols:
            self._symbol_map[s] = unit
        for n in unit.names:
            self._name_map[n] = unit


class SystemRegistry:
    """System Registry"""

    def __init__(self, dimension: type[Dimension]):
        self.dimension = dimension
        self._systemunits: list[SystemUnit] = []

    # Try to find the best fitting unit, picking the largest unit if all units are too small
    def get_best_unit(self, value: Decimal) -> Unit:
        value = abs(value)
        # Pair each unit with the unit following it
        for sunit, nextsunit in zip(self._systemunits[:-1], self._systemunits[1:]):
            # If we're smaller than the next unit's lowest value, then just use this unit
            if value < nextsunit.trigger:
                return sunit.unit
        # If we're too big for all the units, just use the biggest possible unit
        return self._systemunits[-1].unit

    def add_system_unit(self, systemunit: SystemUnit):
        # Insert SystemUnit and keep list sorted
        insort(self._systemunits, systemunit)


class SystemUnit:
    """System Units"""

    def __init__(
        self,
        unit: Unit,
        trigger: Decimal | None = None,
        rel_trigger: Decimal | None = None
    ):
        if trigger is not None and rel_trigger is not None:
            raise ValueError

        self._trigger = trigger
        self._rel_trigger = rel_trigger
        self.unit = unit

    @property
    def factor(self) -> Decimal:
        return self.unit.factor

    @property
    def trigger(self) -> Decimal:
        if self._rel_trigger is not None:
            return self.unit.factor * self._rel_trigger
        if self._trigger is not None:
            return self._trigger
        return self.factor

    def __lt__(self, other: SystemUnit) -> bool:
        return self.trigger < other.trigger

    def __eq__(self, other: SystemUnit) -> bool:
        return self.factor == other.factor

    @classmethod
    def from_json(cls, json: SystemJson, units: UnitRegistry) -> SystemUnit:
        unit = units[json["unit"]]
        trigger = Decimal(json["trigger"]) if "trigger" in json else None
        rel_trigger = Decimal(json["rel_trigger"]) if "rel_trigger" in json else None
        return SystemUnit(unit, trigger, rel_trigger)

DimType = TypeVar("DimType", bound="Dimension")


class Dimension(BaseDecimal):
    """Dimension"""
    _nicename: str
    _units: UnitRegistry
    _systems: dict[str, SystemRegistry]

    def __format__(self, spec: str) -> str:
        value = Decimal(self)
        dSpec = DecimalSpec.parse(spec)
        systems = dSpec.type or ""

        if systems and all(s.casefold() in self._systems.keys() for s in systems):
            dSpec.type = None
            numspec = str(dSpec)

            formattedUnits: list[str] = []
            for s in systems:
                preferName = s.upper() == s
                system = self._systems[s.casefold()]
                unit = system.get_best_unit(value)
                formattedUnits.append(unit.format(value, numspec, preferName))

            # Remove duplicates
            uniqUnits = []
            for u in formattedUnits:
                if u not in uniqUnits:
                    uniqUnits.append(u)
            formatted = " / ".join(uniqUnits)
        else:
            formatted = format(value, spec)

        return formatted

    @classmethod
    def parse(cls: Type[DimType], s: str) -> DimType:
        valueStr, unitStr = cls.get_quantity_pair(s)
        if valueStr is None and unitStr is None:
            raise errors.InvalidSizeValue(s, cls._nicename)
        if valueStr is None:
            valueStr = "1"
        value = Decimal(valueStr)
        unit = cls._units.get(unitStr, None)
        if unit is None:
            raise errors.InvalidSizeValue(s, cls._nicename)
        baseUnit = unit.to_base_unit(value)
        return cls(baseUnit)

    @classmethod
    async def convert(cls: Type[DimType], ctx: BotContext, argument: str) -> DimType:
        return cls.parse(argument)

    @classmethod
    def get_quantity_pair(cls, s: str) -> tuple[str | None, str | None]:
        raise NotImplementedError

    def to_best_unit(self, sysname: str) -> str:
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system.get_best_unit(value)
        return unit.format(value)

    @classmethod
    def load_from_file(cls, filename: str):
        try:
            fileJson = json.loads(pkg_resources.read_text(sizebot.data.units, filename))
        except FileNotFoundError:
            logger.error(f"Error loading {filename}")
            return
        cls._load_from_JSON(fileJson)

    @classmethod
    def _load_from_JSON(cls, json: UnitSystemJson):
        for j in json["units"]:
            unit = Unit.from_json(j)
            cls.add_unit(unit)
        for systemname, systemunits in json["systems"].items():
            for j in systemunits:
                systemunit = SystemUnit.from_json(j, cls._units)
                cls.add_system_unit(systemname, systemunit)

    @classmethod
    def add_unit(cls, unit: Unit):
        cls._units.add_unit(unit)

    @classmethod
    def add_system_unit(cls, systemname: str, systemunit: SystemUnit):
        if systemname not in cls._systems:
            cls._systems[systemname] = SystemRegistry(cls)
        system = cls._systems[systemname]
        system.add_system_unit(systemunit)


class Decimal(BaseDecimal):
    # Decimal + Decimal = Decimal
    def __add__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__add__(other))
        raise NotImplementedError

    # Decimal + Decimal = Decimal
    def __radd__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__radd__(other))
        raise NotImplementedError

    # Decimal - Decimal = Decimal
    def __sub__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__sub__(other))
        raise NotImplementedError

    # Decimal - Decimal = Decimal
    def __rsub__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__rsub__(other))
        raise NotImplementedError

    # Decimal * Decimal = Decimal
    @overload
    def __mul__(self, other: Decimal | int) -> Decimal:
        ...

    # Decimal * SV = SV
    @overload
    def __mul__(self, other: SV) -> SV:
        ...

    # Decimal * WV = WV
    @overload
    def __mul__(self, other: WV) -> WV:
        ...

    # Decimal * TV = TV
    @overload
    def __mul__(self, other: TV) -> TV:
        ...

    # Decimal * AV = AV
    @overload
    def __mul__(self, other: AV) -> AV:
        ...

    # Decimal * VV = VV
    @overload
    def __mul__(self, other: VV) -> VV:
        ...

    # Decimal * RV = RV
    @overload
    def __mul__(self, other: RV) -> RV:
        ...

    def __mul__(self, other: SV | WV | TV | AV | VV | RV | Decimal | int) -> SV | WV | TV | AV | VV | RV | Decimal:
        if isinstance(other, SV):
            return SV(super().__mul__(other))
        if isinstance(other, WV):
            return WV(super().__mul__(other))
        if isinstance(other, TV):
            return TV(super().__mul__(other))
        if isinstance(other, AV):
            return AV(super().__mul__(other))
        if isinstance(other, VV):
            return VV(super().__mul__(other))
        if isinstance(other, RV):
            return RV(super().__mul__(other))
        if isinstance(other, Decimal | int):
            return Decimal(super().__mul__(other))
        raise NotImplementedError

    # Decimal * Decimal = Decimal
    @overload
    def __rmul__(self, other: Decimal | int) -> Decimal:
        ...

    # SV * Decimal = SV
    @overload
    def __rmul__(self, other: SV) -> SV:
        ...

    # WV * Decimal = WV
    @overload
    def __rmul__(self, other: WV) -> WV:
        ...

    # TV * Decimal = TV
    @overload
    def __rmul__(self, other: TV) -> TV:
        ...

    # AV * Decimal = AV
    @overload
    def __rmul__(self, other: AV) -> AV:
        ...

    # VV * Decimal = VV
    @overload
    def __rmul__(self, other: VV) -> VV:
        ...

    # RV * Decimal = RV
    @overload
    def __rmul__(self, other: RV) -> RV:
        ...

    def __rmul__(self, other: SV | WV | TV | AV | VV | RV | Decimal | int) -> SV | WV | TV | AV | VV | RV | Decimal:
        if isinstance(other, SV):
            return SV(super().__rmul__(other))
        if isinstance(other, WV):
            return WV(super().__rmul__(other))
        if isinstance(other, TV):
            return TV(super().__rmul__(other))
        if isinstance(other, AV):
            return AV(super().__rmul__(other))
        if isinstance(other, VV):
            return VV(super().__rmul__(other))
        if isinstance(other, RV):
            return RV(super().__rmul__(other))
        if isinstance(other, Decimal | int):
            return Decimal(super().__rmul__(other))
        raise NotImplementedError

    # Decimal / Decimal = Decimal
    def __truediv__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__truediv__(other))
        raise NotImplementedError

    # Decimal / Decimal = Decimal
    @overload
    def __rtruediv__(self, other: Decimal | int) -> Decimal:
        ...

    # SV / Decimal = SV
    @overload
    def __rtruediv__(self, other: SV) -> SV:
        ...

    # WV / Decimal = WV
    @overload
    def __rtruediv__(self, other: WV) -> WV:
        ...

    # TV / Decimal = TV
    @overload
    def __rtruediv__(self, other: TV) -> TV:
        ...

    # AV / Decimal = AV
    @overload
    def __rtruediv__(self, other: AV) -> AV:
        ...

    # VV / Decimal = VV
    @overload
    def __rtruediv__(self, other: VV) -> VV:
        ...

    # RV / Decimal = RV
    @overload
    def __rtruediv__(self, other: RV) -> RV:
        ...

    def __rtruediv__(self, other: SV | WV | TV | AV | VV | RV | Decimal | int) -> SV | WV | TV | AV | VV | RV | Decimal:
        if isinstance(other, SV):
            return SV(super().__rtruediv__(other))
        if isinstance(other, WV):
            return WV(super().__rtruediv__(other))
        if isinstance(other, TV):
            return TV(super().__rtruediv__(other))
        if isinstance(other, AV):
            return AV(super().__rtruediv__(other))
        if isinstance(other, VV):
            return VV(super().__rtruediv__(other))
        if isinstance(other, RV):
            return RV(super().__rtruediv__(other))
        if isinstance(other, Decimal | int):
            return Decimal(super().__rtruediv__(other))
        raise NotImplementedError

    # Decimal / Decimal = Decimal
    def __floordiv__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # Decimal / Decimal = Decimal
    def __rfloordiv__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # Decimal % Decimal = Decimal
    def __mod__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__mod__(other))
        raise NotImplementedError

    # Decimal % Decimal = Decimal
    def __rmod__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__rmod__(other))
        raise NotImplementedError

    # divmod(Decimal, Decimal) = (Decimal, Decimal)
    def __divmod__(self, other: Decimal | int) -> tuple[Decimal, Decimal]:
        if isinstance(other, Decimal | int):
            quotient, remainder = super().__divmod__(other)
            return Decimal(quotient), Decimal(remainder)
        raise NotImplementedError

    # divmod(Decimal, Decimal) = (Decimal, Decimal)
    def __rdivmod__(self, other: Decimal | int) -> tuple[Decimal, Decimal]:
        if isinstance(other, Decimal | int):
            quotient, remainder = super().__rdivmod__(other)
            return Decimal(quotient), Decimal(remainder)
        raise NotImplementedError

    # Decimal ** Decimal = Decimal
    def __pow__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__pow__(other))
        raise NotImplementedError

    # Decimal ** Decimal = Decimal
    def __rpow__(self, other: Decimal | int) -> Decimal:
        if isinstance(other, Decimal | int):
            return Decimal(super().__rpow__(other))
        raise NotImplementedError

    # Decimal.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # Decimal.sqrt() = Decimal
    def sqrt(self) -> Decimal:
        return Decimal(super().sqrt())


class SV(Dimension):
    """Size Value (length in meters)"""
    _nicename = "size"
    _units = UnitRegistry()
    _systems = {}
    _infinity = RawDecimal("8.79848e53")

    @override
    @classmethod
    def get_quantity_pair(cls, s: str) -> tuple[str | None, str | None]:
        s = remove_brackets(s)
        s = cls.is_feet_and_inches_and_if_so_fix_it(s)
        # TODO: These are temporary patches.
        # Comma patch
        s = s.replace(",", "")
        # Zero patch
        if s.lower() in ["0", "zero", "no"]:
            if s.lower() == "no":
                logger.log(EGG, "No.")
            return "0", "m"
        # Infinity patch
        if s.lower() in ["infinity", "inf", "∞", "yes"]:
            if s.lower() == "yes":
                logger.log(EGG, "Yes.")
            return "infinity", "m"
        # . patch
        if s.startswith("."):
            s = "0" + s
        match = re.match(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\"µ ]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit

    @staticmethod
    def is_feet_and_inches_and_if_so_fix_it(value: str) -> str:
        regex = r"^(?P<feet>\d+\.?\d*)(ft|foot|feet|')(?P<inch>\d+\.?\d*)(in|\")?"
        m = re.match(regex, value, flags = re.I)
        if not m:
            return value
        feetval, inchval = m.group("feet"), m.group("inch")
        if feetval is None and inchval is None:
            return value
        if feetval is None:
            feetval = "0"
        if inchval is None:
            inchval = "0"
        feetval = Decimal(feetval)
        inchval = Decimal(inchval)
        totalinches = (feetval * 12) + inchval
        return f"{str(totalinches)}in"

    # Math Methods
    # SV + SV = SV
    def __add__(self, other: SV) -> SV:
        if isinstance(other, SV):
            return SV(super().__add__(other))
        raise NotImplementedError

    # SV + SV = SV
    def __radd__(self, other: SV) -> SV:
        if isinstance(other, SV):
            return SV(super().__radd__(other))
        raise NotImplementedError

    # SV - SV = SVZ
    def __sub__(self, other: SV) -> SV:
        if isinstance(other, SV):
            return SV(super().__sub__(other))
        raise NotImplementedError

    # SV - SV = SVZ
    def __rsub__(self, other: SV) -> SV:
        if isinstance(other, SV):
            return SV(super().__rsub__(other))
        raise NotImplementedError

    # SV * Decimal = SV
    @overload
    def __mul__(self, other: Decimal | int) -> SV:
        ...

    # SV * SV = AV
    @overload
    def __mul__(self, other: SV) -> AV:
        ...

    # SV * AV = VV
    @overload
    def __mul__(self, other: AV) -> VV:
        ...

    def __mul__(self, other: SV | AV | Decimal | int) -> SV | AV | VV:
        if isinstance(other, Decimal | int):
            return SV(super().__mul__(other))
        if isinstance(other, SV):
            return AV(super().__mul__(other))
        if isinstance(other, AV):
            return VV(super().__mul__(other))
        raise NotImplementedError

    # Decimal * SV  = SV
    @overload
    def __rmul__(self, other: Decimal | int) -> SV:
        ...

    # SV * SV = AV
    @overload
    def __rmul__(self, other: SV) -> AV:
        ...

    # AV * SV = VV
    @overload
    def __rmul__(self, other: AV) -> VV:
        ...

    def __rmul__(self, other: SV | AV | Decimal | int) -> SV | AV | VV:
        if isinstance(other, Decimal | int):
            return SV(super().__rmul__(other))
        if isinstance(other, SV):
            return AV(super().__rmul__(other))
        if isinstance(other, AV):
            return VV(super().__rmul__(other))
        raise NotImplementedError

    # SV / Decimal = SV
    @overload
    def __truediv__(self, other: Decimal | int) -> SV:
        ...

    # SV / SV = Decimal
    @overload
    def __truediv__(self, other: SV) -> Decimal:
        ...

    # SV / TV = RV
    @overload
    def __truediv__(self, other: TV) -> RV:
        ...

    # SV / RV = TV
    @overload
    def __truediv__(self, other: RV) -> TV:
        ...

    def __truediv__(self, other: Decimal | int | SV | TV | RV) -> Decimal | SV | RV | TV:
        if isinstance(other, Decimal | int):
            return SV(super().__truediv__(other))
        if isinstance(other, SV):
            return Decimal(super().__truediv__(other))
        if isinstance(other, TV):
            return RV(super().__truediv__(other))
        if isinstance(other, RV):
            return TV(super().__truediv__(other))
        raise NotImplementedError

    # SV / SV = Decimal
    @overload
    def __rtruediv__(self, other: SV) -> Decimal:
        ...

    # AV / SV = SV
    @overload
    def __rtruediv__(self, other: AV) -> SV:
        ...

    # VV / SV = AV
    @overload
    def __rtruediv__(self, other: VV) -> AV:
        ...

    def __rtruediv__(self, other: SV | AV | VV) -> Decimal | SV | AV:
        if isinstance(other, SV):
            return Decimal(super().__rtruediv__(other))
        if isinstance(other, AV):
            return SV(super().__rtruediv__(other))
        if isinstance(other, VV):
            return AV(super().__rtruediv__(other))
        raise NotImplementedError

    # SV // SV = Decimal
    def __floordiv__(self, other: SV) -> Decimal:
        if isinstance(other, SV):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # SV // SV = Decimal
    def __rfloordiv__(self, other: SV) -> Decimal:
        if isinstance(other, SV):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # SV % SV = SV
    def __mod__(self, other: SV) -> SV:
        if isinstance(other, SV):
            return SV(super().__mod__(other))
        raise NotImplementedError

    # SV % SV = SV
    def __rmod__(self, other: SV) -> SV:
        if isinstance(other, SV):
            return SV(super().__rmod__(other))
        raise NotImplementedError

    # divmod(SV, SV) = (Decimal, SV)
    def __divmod__(self, other: SV) -> tuple[Decimal, SV]:
        if isinstance(other, SV):
            quotient = self.__floordiv__(other)
            remainder = self.__mod__(other)
            return quotient, remainder
        raise NotImplementedError

    # divmod(SV, SV) = (Decimal, SV)
    def __rdivmod__(self, other: SV) -> tuple[Decimal, SV]:
        if isinstance(other, SV):
            quotient = self.__rfloordiv__(other)
            remainder = self.__rmod__(other)
            return quotient, remainder
        raise NotImplementedError

    # SV ** 0 = Decimal
    @overload
    def __pow__(self, other: Literal[0]) -> Decimal:
        ...

    # SV ** 1 = SV
    @overload
    def __pow__(self, other: Literal[1]) -> SV:
        ...

    # SV ** 2 = AV
    @overload
    def __pow__(self, other: Literal[2]) -> AV:
        ...

    # SV ** 3 = VV
    @overload
    def __pow__(self, other: Literal[3]) -> VV:
        ...

    def __pow__(self, other: Literal[0, 1, 2, 3]) -> Decimal | SV | AV | VV:
        if isinstance(other, Decimal | int):
            if other == 0:
                return Decimal(super().__pow__(other))
            if other == 1:
                return SV(super().__pow__(other))
            if other == 2:
                return AV(super().__pow__(other))
            if other == 3:
                return VV(super().__pow__(other))
        raise NotImplementedError

    def __rpow__(self, other: Never) -> Never:
        raise NotImplementedError

    # SV.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # SV.sqrt() = NotImplementedError
    def sqrt(self) -> Never:
        raise NotImplementedError


class WV(Dimension):
    """Weight Value (mass in grams)"""
    _nicename = "weight"
    _units = UnitRegistry()
    _systems = {}

    @override
    @classmethod
    def get_quantity_pair(cls, s: str) -> tuple[str | None, str | None]:
        s = remove_brackets(s)
        # TODO: These are temporary patches.
        # Comma patch
        s = s.replace(",", "")
        # Zero patch
        if s.lower() in ["0", "zero"]:
            return "0", "g"
        # Infinity patch
        if s.lower() in ["infinity", "inf", "∞", "yes"]:
            if s.lower() == "yes":
                logger.log(EGG, "Yes.")
            return "infinity", "g"
        # . patch
        if s.startswith("."):
            s = "0" + s
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\"]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit

    # Math Methods
    # WV + WV = WV
    def __add__(self, other: WV) -> WV:
        if isinstance(other, WV):
            return WV(super().__add__(other))
        raise NotImplementedError

    # WV + WV = WV
    def __radd__(self, other: WV) -> WV:
        if isinstance(other, WV):
            return WV(super().__radd__(other))
        raise NotImplementedError

    # WV - WV = WV
    def __sub__(self, other: WV) -> WV:
        if isinstance(other, WV):
            return WV(super().__sub__(other))
        raise NotImplementedError

    # WV - WV = WV
    def __rsub__(self, other: WV) -> WV:
        if isinstance(other, WV):
            return WV(super().__rsub__(other))
        raise NotImplementedError

    # WV * Decimal = WV
    def __mul__(self, other: Decimal | int) -> WV:
        if isinstance(other, Decimal | int):
            return WV(super().__mul__(other))
        raise NotImplementedError

    # Decimal * WV = WV
    def __rmul__(self, other: Decimal | int) -> WV:
        if isinstance(other, Decimal | int):
            return WV(super().__rmul__(other))
        raise NotImplementedError

    # WV / Decimal = WV
    @overload
    def __truediv__(self, other: Decimal) -> WV:
        ...

    # WV / WV = Decimal
    @overload
    def __truediv__(self, other: WV) -> Decimal:
        ...

    def __truediv__(self, other: Decimal | int | WV) -> Decimal | WV:
        if isinstance(other, Decimal | int):
            return WV(super().__truediv__(other))
        if isinstance(other, WV):
            return Decimal(super().__truediv__(other))
        raise NotImplementedError

    # WV / WV = Decimal
    def __rtruediv__(self, other: WV) -> Decimal:
        if isinstance(other, WV):
            return Decimal(super().__rtruediv__(other))
        raise NotImplementedError

    # WV // WV = Decimal
    def __floordiv__(self, other: WV) -> Decimal:
        if isinstance(other, WV):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # WV // WV = Decimal
    def __rfloordiv__(self, other: WV) -> Decimal:
        if isinstance(other, WV):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # WV % WV = WV
    def __mod__(self, other: WV) -> WV:
        if isinstance(other, WV):
            return WV(super().__mod__(other))
        raise NotImplementedError

    # WV % WV = WV
    def __rmod__(self, other: WV) -> WV:
        if isinstance(other, WV):
            return WV(super().__rmod__(other))
        raise NotImplementedError

    # divmod(WV, WV) = (Decimal, WV)
    def __divmod__(self, other: WV) -> tuple[Decimal, WV]:
        if isinstance(other, WV):
            quotient = self.__floordiv__(other)
            remainder = self.__mod__(other)
            return quotient, remainder
        raise NotImplementedError

    # divmod(WV, WV) = (Decimal, WV)
    def __rdivmod__(self, other: WV) -> tuple[Decimal, WV]:
        if isinstance(other, WV):
            quotient = self.__rfloordiv__(other)
            remainder = self.__rmod__(other)
            return quotient, remainder
        raise NotImplementedError

    # WV ** 0 = Decimal
    @overload
    def __pow__(self, other: Literal[0]) -> Decimal:
        ...

    # WV ** 1 = WV
    @overload
    def __pow__(self, other: Literal[1]) -> WV:
        ...

    def __pow__(self, other: Literal[0, 1]) -> Decimal | WV:
        if isinstance(other, Decimal | int):
            if other == 0:
                return Decimal(super().__pow__(other))
            if other == 1:
                return WV(super().__pow__(other))
        raise NotImplementedError

    def __rpow__(self, other: Never) -> Never:
        raise NotImplementedError

    # WV.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # WV.sqrt() = NotImplementedError
    def sqrt(self) -> Never:
        raise NotImplementedError


class TV(Dimension):
    """Time Value (time in seconds)"""
    _nicename = "time"
    _units = UnitRegistry()
    _systems = {}

    @override
    @classmethod
    def get_quantity_pair(cls, s: str) -> tuple[str | None, str | None]:
        s = remove_brackets(s)
        # . patch
        if s.startswith("."):
            s = "0" + s
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        if value is None:
            value = "1"
        return value, unit

    # Math Methods
    # TV + TV = TV
    def __add__(self, other: TV) -> TV:
        if isinstance(other, TV):
            return TV(super().__add__(other))
        raise NotImplementedError

    # TV + TV = TV
    def __radd__(self, other: TV) -> TV:
        if isinstance(other, TV):
            return TV(super().__radd__(other))
        raise NotImplementedError

    # TV - TV = TV
    def __sub__(self, other: TV) -> TV:
        if isinstance(other, TV):
            return TV(super().__sub__(other))
        raise NotImplementedError

    # TV - TV = TV
    def __rsub__(self, other: TV) -> TV:
        if isinstance(other, TV):
            return TV(super().__rsub__(other))
        raise NotImplementedError

    # TV * Decimal = TV
    @overload
    def __mul__(self, other: Decimal | int) -> TV:
        ...

    # TV * RV = SV
    @overload
    def __mul__(self, other: RV) -> SV:
        ...

    def __mul__(self, other: Decimal | int | RV) -> SV | TV:
        if isinstance(other, Decimal | int):
            return TV(super().__mul__(other))
        if isinstance(other, RV):
            return SV(super().__mul__(other))
        raise NotImplementedError

    # Decimal * TV = TV
    def __rmul__(self, other: Decimal | int) -> TV:
        if isinstance(other, Decimal | int):
            return TV(super().__rmul__(other))
        raise NotImplementedError

    # TV / Decimal = TV
    @overload
    def __truediv__(self, other: Decimal) -> TV:
        ...

    # TV / TV = Decimal
    @overload
    def __truediv__(self, other: TV) -> Decimal:
        ...

    def __truediv__(self, other: Decimal | int | TV) -> Decimal | TV:
        if isinstance(other, Decimal | int):
            return TV(super().__truediv__(other))
        if isinstance(other, TV):
            return Decimal(super().__truediv__(other))
        raise NotImplementedError

    # TV / TV = Decimal
    def __rtruediv__(self, other: TV) -> Decimal:
        if isinstance(other, TV):
            return Decimal(super().__rtruediv__(other))
        raise NotImplementedError

    # TV // TV = Decimal
    def __floordiv__(self, other: TV) -> Decimal:
        if isinstance(other, TV):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # TV // TV = Decimal
    def __rfloordiv__(self, other: TV) -> Decimal:
        if isinstance(other, TV):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # TV % TV = TV
    def __mod__(self, other: TV) -> TV:
        if isinstance(other, TV):
            return TV(super().__mod__(other))
        raise NotImplementedError

    # TV % TV = TV
    def __rmod__(self, other: TV) -> TV:
        if isinstance(other, TV):
            return TV(super().__rmod__(other))
        raise NotImplementedError

    # divmod(TV, TV) = (Decimal, TV)
    def __divmod__(self, other: TV) -> tuple[Decimal, TV]:
        if isinstance(other, TV):
            quotient = self.__floordiv__(other)
            remainder = self.__mod__(other)
            return quotient, remainder
        raise NotImplementedError

    # divmod(TV, TV) = (Decimal, TV)
    def __rdivmod__(self, other: TV) -> tuple[Decimal, TV]:
        if isinstance(other, TV):
            quotient = self.__rfloordiv__(other)
            remainder = self.__rmod__(other)
            return quotient, remainder
        raise NotImplementedError

    # TV ** 0 = Decimal
    @overload
    def __pow__(self, other: Literal[0]) -> Decimal:
        ...

    # TV ** 1 = TV
    @overload
    def __pow__(self, other: Literal[1]) -> TV:
        ...

    def __pow__(self, other: Literal[0, 1]) -> Decimal | TV:
        if isinstance(other, Decimal | int):
            if other == 0:
                return Decimal(super().__pow__(other))
            if other == 1:
                return TV(super().__pow__(other))
        raise NotImplementedError

    def __rpow__(self, other: Never) -> Never:
        raise NotImplementedError

    # TV.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # TV.sqrt() = NotImplementedError
    def sqrt(self) -> Never:
        raise NotImplementedError


class AV(Dimension):
    """Area Value (area in meters-squared)"""
    _nicename = "area"
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def parse(cls, s: str) -> Never:
        raise NotImplementedError

    # Math Methods
    # AV + AV = AV
    def __add__(self, other: AV) -> AV:
        if isinstance(other, AV):
            return AV(super().__add__(other))
        raise NotImplementedError

    # AV + AV = AV
    def __radd__(self, other: AV) -> AV:
        if isinstance(other, AV):
            return AV(super().__radd__(other))
        raise NotImplementedError

    # AV - AV = AV
    def __sub__(self, other: AV) -> AV:
        if isinstance(other, AV):
            return AV(super().__sub__(other))
        raise NotImplementedError

    # AV - AV = AV
    def __rsub__(self, other: AV) -> AV:
        if isinstance(other, AV):
            return AV(super().__rsub__(other))
        raise NotImplementedError

    # AV * Decimal = AV
    @overload
    def __mul__(self, other: Decimal | int) -> AV:
        ...
    
    # AV * SV = VV
    @overload
    def __mul__(self, other: SV) -> VV:
        ...

    def __mul__(self, other: Decimal | int | SV) -> AV | VV:
        if isinstance(other, Decimal | int):
            return AV(super().__mul__(other))
        if isinstance(other, SV):
            return VV(super().__mul__(other))
        raise NotImplementedError

    # Decimal * AV = AV
    @overload
    def __rmul__(self, other: Decimal | int) -> AV:
        ...
    
    # SV * AV = VV
    @overload
    def __rmul__(self, other: SV) -> VV:
        ...

    # Decimal * AV = AV
    def __rmul__(self, other: Decimal | int | SV) -> AV | VV:
        if isinstance(other, Decimal | int):
            return AV(super().__rmul__(other))
        if isinstance(other, SV):
            return VV(super().__rmul__(other))
        raise NotImplementedError

    # AV / Decimal = AV
    @overload
    def __truediv__(self, other: Decimal) -> AV:
        ...

    # AV / SV = SV
    @overload
    def __truediv__(self, other: SV) -> SV:
        ...

    # AV / AV = Decimal
    @overload
    def __truediv__(self, other: AV) -> Decimal:
        ...

    def __truediv__(self, other: Decimal | int | SV | AV) -> Decimal | SV | AV:
        if isinstance(other, Decimal | int):
            return AV(super().__truediv__(other))
        if isinstance(other, SV):
            return SV(super().__truediv__(other))
        if isinstance(other, AV):
            return Decimal(super().__truediv__(other))
        raise NotImplementedError

    # AV / AV = Decimal
    @overload
    def __rtruediv__(self, other: AV) -> Decimal:
        ...
    
    # VV / AV = SV
    @overload
    def __rtruediv__(self, other: VV) -> SV:
        ...

    def __rtruediv__(self, other: AV | VV) -> Decimal | SV:
        if isinstance(other, AV):
            return Decimal(super().__rtruediv__(other))
        if isinstance(other, VV):
            return SV(super().__rtruediv__(other))
        raise NotImplementedError

    # AV // AV = Decimal
    def __floordiv__(self, other: AV) -> Decimal:
        if isinstance(other, AV):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # AV // AV = Decimal
    def __rfloordiv__(self, other: AV) -> Decimal:
        if isinstance(other, AV):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # AV % AV = AV
    def __mod__(self, other: AV) -> AV:
        if isinstance(other, AV):
            return AV(super().__mod__(other))
        raise NotImplementedError

    # AV % AV = AV
    def __rmod__(self, other: AV) -> AV:
        if isinstance(other, AV):
            return AV(super().__rmod__(other))
        raise NotImplementedError

    # divmod(AV, AV) = (Decimal, AV)
    def __divmod__(self, other: AV) -> tuple[Decimal, AV]:
        if isinstance(other, AV):
            quotient = self.__floordiv__(other)
            remainder = self.__mod__(other)
            return quotient, remainder
        raise NotImplementedError

    # divmod(AV, AV) = (Decimal, AV)
    def __rdivmod__(self, other: AV) -> tuple[Decimal, AV]:
        if isinstance(other, AV):
            quotient = self.__rfloordiv__(other)
            remainder = self.__rmod__(other)
            return quotient, remainder
        raise NotImplementedError

    # AV ** 0 = Decimal
    @overload
    def __pow__(self, other: Literal[0]) -> Decimal:
        ...

    # AV ** 1 = AV
    @overload
    def __pow__(self, other: Literal[1]) -> AV:
        ...

    def __pow__(self, other: Literal[0, 1]) -> Decimal | AV:
        if isinstance(other, Decimal | int):
            if other == 0:
                return Decimal(super().__pow__(other))
            if other == 1:
                return AV(super().__pow__(other))
        raise NotImplementedError

    def __rpow__(self, other: Never) -> Never:
        raise NotImplementedError

    # AV.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # AV.sqrt() = SV
    def sqrt(self) -> SV:
        return SV(super().sqrt())


class VV(Dimension):
    """Area Value (area in meters-cubed)"""
    _nicename = "volume"
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def parse(cls, s: str) -> Never:
        raise NotImplementedError

    # Math Methods
    # VV + VV = VV
    def __add__(self, other: VV) -> VV:
        if isinstance(other, VV):
            return VV(super().__add__(other))
        raise NotImplementedError

    # VV + VV = VV
    def __radd__(self, other: VV) -> VV:
        if isinstance(other, VV):
            return VV(super().__radd__(other))
        raise NotImplementedError

    # VV - VV = VV
    def __sub__(self, other: VV) -> VV:
        if isinstance(other, VV):
            return VV(super().__sub__(other))
        raise NotImplementedError

    # VV - VV = VV
    def __rsub__(self, other: VV) -> VV:
        if isinstance(other, VV):
            return VV(super().__rsub__(other))
        raise NotImplementedError

    # VV * Decimal = VV
    def __mul__(self, other: Decimal | int) -> VV:
        if isinstance(other, Decimal | int):
            return VV(super().__mul__(other))
        raise NotImplementedError

    # Decimal * VV = VV
    def __rmul__(self, other: Decimal | int) -> VV:
        if isinstance(other, Decimal | int):
            return VV(super().__rmul__(other))
        raise NotImplementedError

    # VV / Decimal = VV
    @overload
    def __truediv__(self, other: Decimal) -> VV:
        ...

    # VV / SV = AV
    @overload
    def __truediv__(self, other: SV) -> AV:
        ...

    # VV / AV = SV
    @overload
    def __truediv__(self, other: AV) -> SV:
        ...

    # VV / VV = Decimal
    @overload
    def __truediv__(self, other: VV) -> Decimal:
        ...

    def __truediv__(self, other: Decimal | int | SV | AV | VV) -> Decimal | SV | AV | VV:
        if isinstance(other, Decimal | int):
            return VV(super().__truediv__(other))
        if isinstance(other, SV):
            return AV(super().__truediv__(other))
        if isinstance(other, AV):
            return SV(super().__truediv__(other))
        if isinstance(other, VV):
            return Decimal(super().__truediv__(other))
        raise NotImplementedError

    # VV / VV = Decimal
    def __rtruediv__(self, other: VV) -> Decimal:
        if isinstance(other, VV):
            return Decimal(super().__rtruediv__(other))
        raise NotImplementedError

    # VV // VV = Decimal
    def __floordiv__(self, other: VV) -> Decimal:
        if isinstance(other, VV):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # VV // VV = Decimal
    def __rfloordiv__(self, other: VV) -> Decimal:
        if isinstance(other, VV):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # VV % VV = VV
    def __mod__(self, other: VV) -> VV:
        if isinstance(other, VV):
            return VV(super().__mod__(other))
        raise NotImplementedError

    # VV % VV = VV
    def __rmod__(self, other: VV) -> VV:
        if isinstance(other, VV):
            return VV(super().__rmod__(other))
        raise NotImplementedError

    # divmod(VV, VV) = (Decimal, VV)
    def __divmod__(self, other: VV) -> tuple[Decimal, VV]:
        if isinstance(other, VV):
            quotient = self.__floordiv__(other)
            remainder = self.__mod__(other)
            return quotient, remainder
        raise NotImplementedError

    # divmod(VV, VV) = (Decimal, VV)
    def __rdivmod__(self, other: VV) -> tuple[Decimal, VV]:
        if isinstance(other, VV):
            quotient = self.__rfloordiv__(other)
            remainder = self.__rmod__(other)
            return quotient, remainder
        raise NotImplementedError

    # VV ** 0 = Decimal
    @overload
    def __pow__(self, other: Literal[0]) -> Decimal:
        ...

    # VV ** 1 = VV
    @overload
    def __pow__(self, other: Literal[1]) -> VV:
        ...

    def __pow__(self, other: Literal[0, 1]) -> Decimal | VV:
        if isinstance(other, Decimal | int):
            if other == 0:
                return Decimal(super().__pow__(other))
            if other == 1:
                return VV(super().__pow__(other))
        raise NotImplementedError

    def __rpow__(self, other: Never) -> Never:
        raise NotImplementedError

    # VV.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # VV.sqrt() = NotImplementedError
    def sqrt(self) -> Never:
        raise NotImplementedError


class RV(Dimension):
    """Speed Value (meters per second)"""
    _nicename = "speed"
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def parse(cls, s: str) -> Never:
        raise NotImplementedError

    # Math Methods
    # RV + RV = RV
    def __add__(self, other: RV) -> RV:
        if isinstance(other, RV):
            return RV(super().__add__(other))
        raise NotImplementedError

    # RV + RV = RV
    def __radd__(self, other: RV) -> RV:
        if isinstance(other, RV):
            return RV(super().__radd__(other))
        raise NotImplementedError

    # RV - RV = RV
    def __sub__(self, other: RV) -> RV:
        if isinstance(other, RV):
            return RV(super().__sub__(other))
        raise NotImplementedError

    # RV - RV = RV
    def __rsub__(self, other: RV) -> RV:
        if isinstance(other, RV):
            return RV(super().__rsub__(other))
        raise NotImplementedError

    # RV * TV = SV
    @overload
    def __mul__(self, other: TV) -> SV:
        ...

    # RV * Decimal = RV
    @overload
    def __mul__(self, other: Decimal | int) -> RV:
        ...

    # RV * Decimal = RV
    def __mul__(self, other: Decimal | int | TV) -> SV | RV:
        if isinstance(other, Decimal | int):
            return RV(super().__mul__(other))
        if isinstance(other, TV):
            return SV(super().__mul__(other))
        raise NotImplementedError

    # TV * RV = SV
    @overload
    def __rmul__(self, other: TV) -> SV:
        ...

    # Decimal * RV = RV
    @overload
    def __rmul__(self, other: Decimal | int) -> RV:
        ...

    # Decimal * RV = RV
    def __rmul__(self, other: Decimal | int | TV) -> SV | RV:
        if isinstance(other, Decimal | int):
            return RV(super().__rmul__(other))
        if isinstance(other, TV):
            return SV(super().__rmul__(other))
        raise NotImplementedError

    # RV / Decimal = RV
    @overload
    def __truediv__(self, other: Decimal) -> RV:
        ...

    # RV / RV = Decimal
    @overload
    def __truediv__(self, other: RV) -> Decimal:
        ...

    def __truediv__(self, other: Decimal | int | RV) -> Decimal | RV:
        if isinstance(other, Decimal | int):
            return RV(super().__truediv__(other))
        if isinstance(other, RV):
            return Decimal(super().__truediv__(other))
        raise NotImplementedError

    # RV / RV = Decimal
    def __rtruediv__(self, other: RV) -> Decimal:
        if isinstance(other, RV):
            return Decimal(super().__rtruediv__(other))
        raise NotImplementedError

    # RV // RV = Decimal
    def __floordiv__(self, other: RV) -> Decimal:
        if isinstance(other, RV):
            return Decimal(super().__floordiv__(other))
        raise NotImplementedError

    # RV // RV = Decimal
    def __rfloordiv__(self, other: RV) -> Decimal:
        if isinstance(other, RV):
            return Decimal(super().__rfloordiv__(other))
        raise NotImplementedError

    # RV % RV = RV
    def __mod__(self, other: RV) -> RV:
        if isinstance(other, RV):
            return RV(super().__mod__(other))
        raise NotImplementedError

    # RV % RV = RV
    def __rmod__(self, other: RV) -> RV:
        if isinstance(other, RV):
            return RV(super().__rmod__(other))
        raise NotImplementedError

    # divmod(RV, RV) = (Decimal, RV)
    def __divmod__(self, other: RV) -> tuple[Decimal, RV]:
        if isinstance(other, RV):
            quotient = self.__floordiv__(other)
            remainder = self.__mod__(other)
            return quotient, remainder
        raise NotImplementedError

    # divmod(RV, RV) = (Decimal, RV)
    def __rdivmod__(self, other: RV) -> tuple[Decimal, RV]:
        if isinstance(other, RV):
            quotient = self.__rfloordiv__(other)
            remainder = self.__rmod__(other)
            return quotient, remainder
        raise NotImplementedError

    # RV ** 0 = Decimal
    @overload
    def __pow__(self, other: Literal[0]) -> Decimal:
        ...

    # RV ** 1 = RV
    @overload
    def __pow__(self, other: Literal[1]) -> RV:
        ...

    def __pow__(self, other: Literal[0, 1]) -> Decimal | RV:
        if isinstance(other, Decimal | int):
            if other == 0:
                return Decimal(super().__pow__(other))
            if other == 1:
                return RV(super().__pow__(other))
        raise NotImplementedError

    def __rpow__(self, other: Never) -> Never:
        raise NotImplementedError

    # RV.log10() = Decimal
    def log10(self) -> Decimal:
        return Decimal(super().log10())

    # RV.sqrt() = NotImplementedError
    def sqrt(self) -> Never:
        raise NotImplementedError


INCH = Decimal("0.0254")

def load_json_file(filename: str) -> Any | None:
    try:
        units_JSON = json.loads(pkg_resources.read_text(sizebot.data, filename))
    except FileNotFoundError:
        units_JSON = None
    return units_JSON


def pos_SV(s: str) -> SV:
    value = SV.parse(s)
    if value < 0:
        raise errors.InvalidSizeValue(s, "SV")
    return value


def pos_WV(s: str) -> WV:
    value = WV.parse(s)
    if value < 0:
        raise errors.InvalidSizeValue(s, "WV")
    return value


def init():
    SV.load_from_file("sv.json")
    feetAndInches = FeetAndInchesUnit()
    SV.add_unit(feetAndInches)
    SV.add_system_unit(systemname="u", systemunit=SystemUnit(unit=feetAndInches))
    WV.load_from_file("wv.json")
    TV.load_from_file("tv.json")
    AV.load_from_file("av.json")
    VV.load_from_file("vv.json")
