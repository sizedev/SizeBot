import json
import re
import collections
import importlib.resources as pkg_resources

from sizebot.digidecimal import Decimal, DecimalSpec
from sizebot import digierror as errors
from sizebot.utils import removeBrackets, re_num, tryOrNone, iset
from sizebot.picker import getRandomCloseUnit
import sizebot.digilogger as logger

from sizebot import units as units_dir

__all__ = ["Rate", "Mult", "SV", "WV", "TV"]


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
    re_num_unit = f"{re_num} *[A-Za-z]+"
    re_opnum_unit = f"({re_num})? *[A-Za-z]+"

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
            raise errors.InvalidSizeValue(s)
        prefix = match.group("prefix")
        multOrSvStr = match.group("multOrSv")
        tvStr = match.group("tv")
        stopStr = match.group("stop")

        isSub = prefix in cls.subPrefixes

        valueSV = tryOrNone(SV.parse, multOrSvStr, ignore=errors.InvalidSizeValue)
        valueMult = None
        if valueSV is None:
            valueMult = tryOrNone(Mult.parse, multOrSvStr, ignore=errors.InvalidSizeValue)
        if valueSV is None and valueMult is None:
            raise errors.InvalidSizeValue(s)
        if valueSV and isSub:
            valueSV = -valueSV

        valueTV = tryOrNone(TV.parse, tvStr, ignore=errors.InvalidSizeValue)
        if valueTV is None:
            raise errors.InvalidSizeValue(s)

        stopSV = None
        stopTV = None
        if stopStr is not None:
            stopSV = tryOrNone(SV.parse, stopStr, ignore=errors.InvalidSizeValue)
            if stopSV is None:
                stopTV = tryOrNone(TV.parse, stopStr, ignore=errors.InvalidSizeValue)
            if stopSV is None and stopTV is None:
                raise errors.InvalidSizeValue(s)

        if valueSV is not None:
            addPerSec = valueSV / valueTV
        else:
            addPerSec = Decimal("0")

        if valueMult is not None:
            mulPerSec = valueMult ** (1 / valueTV)
        else:
            mulPerSec = Decimal("1")

        return addPerSec, mulPerSec, stopSV, stopTV


class Mult():
    """Mult"""
    multPrefixes = ["x", "X", "*", "times", "mult", "multiply"]
    divPrefixes = ["/", "÷", "div", "divide"]
    prefixes = '|'.join(re.escape(p) for p in multPrefixes + divPrefixes)
    suffixes = '|'.join(re.escape(p) for p in ["x", "X"])
    re_mult = re.compile(f"(?P<prefix>{prefixes})? *(?P<multValue>{re_num}) *(?P<suffix>{suffixes})?")

    @classmethod
    def parse(cls, s):
        match = cls.re_mult.match(s)
        if match is None:
            raise errors.InvalidSizeValue(s)
        prefix = match.group("prefix") or match.group("suffix")
        multValue = Decimal(match.group("multValue"))

        isDivide = prefix in cls.divPrefixes
        if isDivide:
            multValue = 1 / multValue

        return multValue


class Unit():
    """Formats a value by scaling it and applying the appropriate symbol suffix"""

    hidden = False

    def __init__(self, factor="1", symbol=None, name=None, namePlural=None, symbols=[], names=[], fractional=False):
        self.fractional = fractional
        self.factor = Decimal(factor)

        self.symbol = symbol
        self.name = name
        self.namePlural = namePlural

        self.symbols = {s.strip() for s in symbols}  # case sensitive symbols
        if symbol is not None:
            self.symbols.add(symbol.strip())

        self.names = iset(n.strip() for n in names)        # case insensitive names
        if name is not None:
            self.names.add(name.strip())
        if namePlural is not None:
            self.names.add(namePlural.strip())

    def format(self, value, spec="", preferName=False):
        scaled = Decimal(value / self.factor)
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

    def toBaseUnit(self, v):
        return v * self.factor

    def isUnit(self, u):
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


class FixedUnit(Unit):
    """Unit that only formats to a single symbol"""

    def format(self, value, accuracy=2, spec="", preferName=False, useFractional=False):
        return self.symbol

    def toBaseUnit(self, v):
        return self.factor


class FeetAndInchesUnit(Unit):
    """Unit for handling feet and inches"""
    hidden = True

    def __init__(self):
        self.inch = Decimal("0.0254")
        foot = self.inch * Decimal("12")
        self.factor = foot
        self.symbol = ("'", "\"")

    def format(self, value, spec="", preferName=False):
        inchval = value / self.inch                  # convert to inches
        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches

        feetSpec = DecimalSpec.parse(spec)
        feetSpec.precision = "0"

        inchSpec = DecimalSpec.parse(spec)
        inchSpec.sign = None

        formatted = f"{Decimal(feetval):{feetSpec}}'{Decimal(inchval):{inchSpec}}\""
        return formatted

    def toBaseUnit(self, v):
        return None

    def isUnit(self, u):
        return u == self.symbol


class UnitRegistry(collections.abc.Mapping):
    """Unit Registry"""

    def __init__(self):
        self._units = []

    def __getitem__(self, key):
        try:
            return next(unit for unit in self._units if unit.isUnit(key))
        except StopIteration:
            raise KeyError(key)

    def __contains__(self, name):
        return self[name] is not None

    def __iter__(self):
        return iter(unit for unit in self._units if not unit.hidden)

    def __len__(self):
        return len(self._units)

    def addUnit(self, unit):
        self._units.append(unit)


class SystemRegistry():
    """System Registry"""

    def __init__(self, dimension):
        self.dimension = dimension
        self._systemunits = []
        self.isSorted = False

    # Try to find the best fitting unit, picking the largest unit if all units are too small
    def getBestUnit(self, value):
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
    def getGoodUnit(self, value):
        if not self.isSorted:
            self._systemunits.sort()
        systemunit = getRandomCloseUnit(value, self._systemunits)
        if systemunit is None:
            return self.getBestUnit(value)
        return systemunit.unit

    def addSystemUnit(self, systemunit):
        self.isSorted = False
        self._systemunits.append(systemunit)
        systemunit.load(self.dimension._units)


class SystemUnit():
    """System Units"""

    def __init__(self, unit, trigger=None):
        self.unitname = unit
        self._trigger = trigger and Decimal(trigger)
        self.unit = None

    def load(self, units):
        self.unit = units[self.unitname]

    @property
    def factor(self):
        return self.unit.factor

    @property
    def trigger(self):
        if self._trigger is not None:
            return self._trigger
        return self.factor

    def __lt__(self, other):
        return self.trigger < other.trigger


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
                unit = system.getBestUnit(value)
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
        value, unitStr = cls.getQuantityPair(s)
        if value is None and unitStr is None:
            raise errors.InvalidSizeValue(s)
        if value is None:
            value = Decimal("1")
        else:
            value = Decimal(value)
        unit = cls._units.get(unitStr, None)
        if unit is None:
            raise errors.InvalidSizeValue(s)
        baseUnit = unit.toBaseUnit(value)
        return cls(baseUnit)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)

    @classmethod
    def getQuantityPair(cls, s):
        raise NotImplementedError

    def toBestUnit(self, sysname, *args, **kwargs):
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system.getBestUnit(value)
        return unit.format(value, *args, **kwargs)

    def toGoodUnit(self, sysname, *args, **kwargs):
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system.getGoodUnit(value)
        return unit.format(value, *args, **kwargs)

    def toUnit(self, sysname, unitname, *args, **kwargs):
        value = Decimal(self)
        system = self._systems[sysname]
        unit = system[unitname]
        return unit.format(value, *args, **kwargs)

    @classmethod
    async def loadFromFile(cls, filename):
        try:
            fileJson = json.loads(pkg_resources.read_text(units_dir, filename))
        except FileNotFoundError:
            await logger.error(f"Error loading {filename}")
            return
        cls.loadFromJson(fileJson)

    @classmethod
    def loadFromJson(cls, json):
        for u in json["units"]:
            cls.addUnitFromJson(**u)
        for systemname, systemunits in json["systems"].items():
            for u in systemunits:
                cls.addSystemUnitFromJson(systemname, **u)

    @classmethod
    def addUnitFromJson(cls, **kwargs):
        unit = Unit(**kwargs)
        cls.addUnit(unit)

    @classmethod
    def addUnit(cls, unit):
        cls._units.addUnit(unit)

    @classmethod
    def addSystemUnitFromJson(cls, systemname, **kwargs):
        systemunit = SystemUnit(**kwargs)
        cls.addSystemUnit(systemname, systemunit)

    @classmethod
    def addSystemUnit(cls, systemname, systemunit):
        system = cls.getOrAddSystem(systemname)
        system.addSystemUnit(systemunit)

    @classmethod
    def getOrAddSystem(cls, systemname):
        system = cls._systems.get(systemname)
        if system is None:
            system = SystemRegistry(cls)
            cls._systems[systemname] = system
        return system


class SV(Dimension):
    """Size Value (length in meters)"""
    _units = UnitRegistry()
    _systems = {}
    infinity = Decimal("8.79848e53")

    @classmethod
    def getQuantityPair(cls, s):
        s = removeBrackets(s)
        s = cls.isFeetAndInchesAndIfSoFixIt(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\" ]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit

    @staticmethod
    def isFeetAndInchesAndIfSoFixIt(value):
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
        totalinches = (Decimal(feetval) * Decimal("12")) + Decimal(inchval)
        return f"{totalinches}in"

    def __repr__(self):
        return f"SV('{self}')"


class WV(Dimension):
    """Weight Value (mass in grams)"""
    _units = UnitRegistry()
    _systems = {}
    infinity = Decimal("3.4e84")

    @classmethod
    def getQuantityPair(cls, s):
        s = removeBrackets(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\"]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit

    def __repr__(self):
        return f"WV('{self}')"


class TV(Dimension):
    """Time Value (time in seconds)"""
    _units = UnitRegistry()
    _systems = {}

    @classmethod
    def getQuantityPair(cls, s):
        s = removeBrackets(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        if value is None:
            value = "1"
        return value, unit

    def __repr__(self):
        return f"TV('{self}')"


def loadJsonFile(filename):
    try:
        unitsJson = json.loads(pkg_resources.read_text(units_dir, filename))
    except FileNotFoundError:
        unitsJson = None
    return unitsJson


async def init():
    await SV.loadFromFile("sv.json")
    SV.addUnit(FeetAndInchesUnit())
    SV.addSystemUnit(systemname="u", systemunit=SystemUnit(unit=("'", "\"")))
    await WV.loadFromFile("wv.json")
    await TV.loadFromFile("tv.json")
