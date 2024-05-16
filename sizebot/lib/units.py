from typing import Tuple
from collections import Mapping

import importlib.resources as pkg_resources
import json
import logging
import re
from functools import total_ordering

from discord.ext import commands

from sizebot.lib.loglevels import EGG
import sizebot.data
import sizebot.data.units
from sizebot.lib import errors, utils
from sizebot.lib.digidecimal import Decimal, DecimalSpec
from sizebot.lib.picker import get_random_close_unit


__all__ = ["Rate", "Mult", "SV", "WV", "TV", "AV", "VV"]

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


class Rate():
    """Rate"""
    re_num_unit = f"{utils.re_num} *[A-Za-z]+"
    re_opnum_unit = f"({utils.re_num})? *[A-Za-z]+"

    rateDividers = "|".join(re.escape(d) for d in ("/", "per", "every"))
    stopDividers = "|".join(re.escape(d) for d in ("until", "for", "->"))
    addPrefixes = ["+", "plus", "add"]
    subPrefixes = ["-", "minus", "subtract", "sub"]
    addSubPrefixes = "|".join(re.escape(d) for d in addPrefixes + subPrefixes)
    re_rate = re.compile(f"(?P<prefix>{addSubPrefixes})? *(?P<multOrSv>.*) *({rateDividers}) *(?P<tv>{re_opnum_unit}) *(({stopDividers}) *(?P<stop>{re_opnum_unit}))?")

    @classmethod
    def parse(cls, s):
        match = cls.re_rate.match(s)
        if match is None:
            raise errors.InvalidSizeValue(s, "rate")
        prefix = match.group("prefix")
        multOrSvStr = match.group("multOrSv")
        tvStr = match.group("tv")
        stopStr = match.group("stop")

        isSub = prefix in cls.subPrefixes

        valueSV = utils.try_or_none(SV.parse, multOrSvStr, ignore=errors.InvalidSizeValue)
        valueMult = None
        if valueSV is None:
            valueMult = utils.try_or_none(Mult.parse, multOrSvStr, ignore=errors.InvalidSizeValue)
        if valueSV is None and valueMult is None:
            raise errors.InvalidSizeValue(s, "size")
        if valueSV and isSub:
            valueSV = -valueSV

        valueTV = utils.try_or_none(TV.parse, tvStr, ignore=errors.InvalidSizeValue)
        if valueTV is None:
            raise errors.InvalidSizeValue(s, "time")

        stopSV = None
        stopTV = None
        if stopStr is not None:
            stopSV = utils.try_or_none(SV.parse, stopStr, ignore=errors.InvalidSizeValue)
            if stopSV is None:
                stopTV = utils.try_or_none(TV.parse, stopStr, ignore=errors.InvalidSizeValue)
            if stopSV is None and stopTV is None:
                raise errors.InvalidSizeValue(s, "stop")

        if valueSV is not None:
            addPerSec = valueSV / valueTV
        else:
            addPerSec = 0

        if valueMult is not None:
            mulPerSec = valueMult ** (1 / valueTV)
        else:
            mulPerSec = 1

        return Decimal(addPerSec), Decimal(mulPerSec), stopSV, stopTV


class Mult():
    """Mult"""
    multPrefixes = ["x", "X", "*", "times", "mult", "multiply"]
    divPrefixes = ["/", "÷", "div", "divide"]
    prefixes = '|'.join(re.escape(p) for p in multPrefixes + divPrefixes)
    suffixes = '|'.join(re.escape(p) for p in ["x", "X", "%"])
    re_mult = re.compile(f"(?P<prefix>{prefixes})? *(?P<multValue>{utils.re_num}) *(?P<suffix>{suffixes})?")

    @classmethod
    def parse(cls, s):
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


@total_ordering
class Unit():
    """Formats a value by scaling it and applying the appropriate symbol suffix"""

    hidden = False

    def __init__(self, factor=1, symbol=None, name=None, namePlural=None, symbols=[], names=[], fractional=False):
        self.fractional = fractional
        self.factor = Decimal(factor)

        self.symbol = symbol
        self.name = name
        self.namePlural = namePlural

        self.symbols = {s.strip() for s in symbols}  # case sensitive symbols
        if symbol is not None:
            self.symbols.add(symbol.strip())

        self.names = utils.iset(n.strip() for n in names)  # case insensitive names
        if name is not None:
            self.names.add(name.strip())
        if namePlural is not None:
            self.names.add(namePlural.strip())

    def format(self, value, spec="", preferName=False):
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

    def to_base_unit(self, v):
        return v * self.factor

    def is_unit(self, u):
        if isinstance(u, str):
            u = u.strip()
        return isinstance(u, str) and (u in self.names or u in self.symbols)

    @property
    def id(self):
        return self.symbol or self.name or self.namePlural

    def __str__(self):
        if self.name is not None and self.symbol is not None:
            return f"{self.name.strip()} ({self.symbol.strip()})"
        if self.name is not None:
            return self.name.strip()
        if self.symbol is not None:
            return self.symbol.strip()
        return "?"

    def __lt__(self, other):
        return self.factor < other.factor

    def __eq__(self, other):
        return self.factor == other.factor


class FixedUnit(Unit):
    """Unit that only formats to a single symbol"""

    def format(self, value, spec="", preferName=False):
        return self.symbol

    def to_base_unit(self, v):
        return self.factor


class FeetAndInchesUnit(Unit):
    """Unit for handling feet and inches"""
    hidden = True

    def __init__(self):
        self.inch = Decimal("0.0254")
        foot = self.inch * 12
        self.factor = foot
        self.symbol = ("'", "\"")

    def format(self, value, spec="", preferName=False):
        feetSpec = DecimalSpec.parse(spec)
        feetSpec.precision = "0"

        inchSpec = DecimalSpec.parse(spec)
        inchSpec.sign = None

        inchval = value / self.inch             # convert to inches
        precision = 2
        if inchSpec.precision is not None:
            precision = int(inchSpec.precision)
        inchval = round(inchval, precision)

        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches
        if inchval < Decimal("1e-100"):
            inchval = Decimal("0")

        formatted = f"{feetval:{feetSpec}}'{inchval:{inchSpec}}\""
        return formatted

    def to_base_unit(self, v):
        return None

    def is_unit(self, u):
        return u == self.symbol


class UnitRegistry(Mapping):
    """Unit Registry"""

    def __init__(self):
        self._units = []

    def __getitem__(self, key):
        try:
            return next(unit for unit in self._units if unit.is_unit(key))
        except StopIteration:
            raise KeyError(key)

    def __contains__(self, name):
        return self[name] is not None

    def __iter__(self):
        return iter(unit for unit in self._units if not unit.hidden)

    def __len__(self):
        return len(self._units)

    def add_unit(self, unit):
        self._units.append(unit)


class SystemRegistry():
    """System Registry"""

    def __init__(self, dimension):
        self.dimension = dimension
        self._systemunits = []
        self.isSorted = False

    # Try to find the best fitting unit, picking the largest unit if all units are too small
    def get_best_unit(self, value):
        if not self.isSorted:
            self._systemunits.sort()
        value = abs(value)
        # Pair each unit with the unit following it
        for sunit, nextsunit in zip(self._systemunits[:-1], self._systemunits[1:]):
            # If we're smaller than the next unit's lowest value, then just use this unit
            if value < nextsunit.trigger:
                return sunit.unit
        # If we're too big for all the units, just use the biggest possible unit
        return self._systemunits[-1].unit

    # Try to find the best fitting unit, picking the largest unit if all units are too small
    def get_good_unit(self, value, options = 6):
        if not self.isSorted:
            self._systemunits.sort()
        systemunit = get_random_close_unit(value, self._systemunits, options)
        if systemunit is None:
            return self.get_best_unit(value)
        return systemunit.unit

    def add_system_unit(self, systemunit):
        self.isSorted = False
        self._systemunits.append(systemunit)
        systemunit.load(self.dimension._units)


class SystemUnit():
    """System Units"""

    def __init__(self, unit, trigger=None, rel_trigger=None):
        if trigger is not None and rel_trigger is not None:
            raise ValueError

        self.unitname = unit
        self._trigger = trigger and Decimal(trigger)
        self._rel_trigger = rel_trigger and Decimal(rel_trigger)
        self.unit = None

    def load(self, units):
        self.unit = units[self.unitname]

    @property
    def factor(self):
        return self.unit.factor

    @property
    def trigger(self):
        if self._rel_trigger is not None:
            return self.unit.factor * self._rel_trigger
        if self._trigger is not None:
            return self._trigger
        return self.factor

    def __lt__(self, other):
        return self.trigger < other.trigger

    def __eq__(self, other):
        return self.factor == other.factor


class Dimension(Decimal):
    """Dimension"""

    def __format__(self, spec):
        value = Decimal(self)
        dSpec = DecimalSpec.parse(spec)

        systems = dSpec.type or ""

        if systems and all(s.casefold() in self._systems.keys() for s in systems):
            dSpec.type = None
            numspec = str(dSpec)

            formattedUnits = []
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
    def parse(cls, s):
        value, unitStr = cls.get_quantity_pair(s)
        kinds = {"SV": "size", "WV": "weight", "TV": "time"}
        kind = kinds.get(cls.__name__, cls.__name__)
        if value is None and unitStr is None:
            raise errors.InvalidSizeValue(s, kind)
        if value is None:
            value = Decimal(1)
        else:
            value = Decimal(value)
        unit = cls._units.get(unitStr, None)
        if unit is None:
            raise errors.InvalidSizeValue(s, kind)
        baseUnit = unit.to_base_unit(value)
        return cls(baseUnit)

    @classmethod
    async def convert(cls, ctx: commands.Context, argument):
        return cls.parse(argument)

    @classmethod
    def get_quantity_pair(cls, s) -> Tuple:
        raise NotImplementedError

    def to_best_unit(self, sysname, *args, **kwargs):
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system.get_best_unit(value)
        return unit.format(value, *args, **kwargs)

    def to_good_unit(self, sysname, options = 6, *args, **kwargs):
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system.get_good_unit(value, options)
        return unit.format(value, *args, **kwargs)

    def to_unit(self, sysname, unitname, *args, **kwargs):
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system[unitname]
        return unit.format(value, *args, **kwargs)

    @classmethod
    def load_from_file(cls, filename):
        try:
            fileJson = json.loads(pkg_resources.read_text(sizebot.data.units, filename))
        except FileNotFoundError:
            logger.error(f"Error loading {filename}")
            return
        cls.load_from_JSON(fileJson)

    @classmethod
    def load_from_JSON(cls, json):
        for u in json["units"]:
            cls.add_unit_from_JSON(**u)
        for systemname, systemunits in json["systems"].items():
            for u in systemunits:
                cls.add_system_unit_from_JSON(systemname, **u)

    @classmethod
    def add_unit_from_JSON(cls, **kwargs):
        unit = Unit(**kwargs)
        cls.add_unit(unit)

    @classmethod
    def add_unit(cls, unit):
        cls._units.add_unit(unit)

    @classmethod
    def add_system_unit_from_JSON(cls, systemname, **kwargs):
        systemunit = SystemUnit(**kwargs)
        cls.add_system_unit(systemname, systemunit)

    @classmethod
    def add_system_unit(cls, systemname, systemunit):
        system = cls.get_or_add_system(systemname)
        system.add_system_unit(systemunit)

    @classmethod
    def get_or_add_system(cls, systemname):
        system = cls._systems.get(systemname)
        if system is None:
            system = SystemRegistry(cls)
            cls._systems[systemname] = system
        return system

    def __repr__(self):
        return f"{type(self).__name__}('{self}')"


class SV(Dimension):
    """Size Value (length in meters)"""
    _units = UnitRegistry()
    _systems = {}
    _infinity = Decimal("8.79848e53")

    @classmethod
    def get_quantity_pair(cls, s):
        s = utils.remove_brackets(s)
        s = cls.is_feet_and_inches_and_if_so_fix_it(s)
        # TODO: These are temporary patches.
        # Comma patch
        s = s.replace(",", "")
        # Zero patch
        if s.lower() in ["0", "zero", "no"]:
            if s.lower() == "no":
                logger.log(EGG, "No.")
            return 0, "m"
        # Infinity patch
        if s.lower() in ["infinity", "inf", "∞", "yes"]:
            if s.lower() == "yes":
                logger.log(EGG, "Yes.")
            return cls._infinity, "m"
        # . patch
        if s.startswith("."):
            s = "0" + s
        match = re.match(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\"µ ]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit

    @staticmethod
    def is_feet_and_inches_and_if_so_fix_it(value):
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


class WV(Dimension):
    """Weight Value (mass in grams)"""
    _units = UnitRegistry()
    _systems = {}
    _infinity = Decimal("1e1000")

    @classmethod
    def get_quantity_pair(cls, s):
        s = utils.remove_brackets(s)
        # TODO: These are temporary patches.
        # Comma patch
        s = s.replace(",", "")
        # Zero patch
        if s.lower() in ["0", "zero"]:
            return 0, "g"
        # Infinity patch
        if s.lower() in ["infinity", "inf", "∞", "yes"]:
            if s.lower() == "yes":
                logger.log(EGG, "Yes.")
            return cls._infinity, "g"
        # . patch
        if s.startswith("."):
            s = "0" + s
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\"]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit


class TV(Dimension):
    """Time Value (time in seconds)"""
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def get_quantity_pair(cls, s):
        s = utils.remove_brackets(s)
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


class AV(Dimension):
    """Area Value (area in meters-squared)"""
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def parse(cls, s: str):
        raise NotImplementedError


class VV(Dimension):
    """Area Value (area in meters-cubed)"""
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def parse(cls, s: str):
        raise NotImplementedError


def load_json_file(filename):
    try:
        units_JSON = json.loads(pkg_resources.read_text(sizebot.data, filename))
    except FileNotFoundError:
        units_JSON = None
    return units_JSON


def init():
    SV.load_from_file("sv.json")
    SV.add_unit(FeetAndInchesUnit())
    SV.add_system_unit(systemname="u", systemunit=SystemUnit(unit=("'", "\"")))
    WV.load_from_file("wv.json")
    TV.load_from_file("tv.json")
    AV.load_from_file("av.json")
    VV.load_from_file("vv.json")
