import re

from sizebot.digidecimal import Decimal, roundDecimal, trimzeroes
from sizebot import digierror as errors
from sizebot.utils import removeBrackets, re_num, parseSpec, buildSpec, tryOrNone, iset

__all__ = ["Rate", "Mult", "SV", "WV", "TV"]


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
    def parseRate(cls, s):
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


# Unit: Formats a value by scaling it and applying the appropriate symbol suffix
class Unit():
    """Unit"""

    def __init__(self, factor=Decimal("1"), symbol=None, name=None, namePlural=None, symbols=[], names=[]):
        self.factor = factor

        self.symbol = symbol
        self.name = name
        self.namePlural = namePlural

        self.symbols = set(symbols)     # case sensitive symbols
        if symbol is not None:
            self.symbols.add(symbol)

        self.names = iset(names)        # case insensitive names
        if name is not None:
            self.names.add(name)
        if namePlural is not None:
            self.names.add(namePlural)

    def format(self, value, accuracy=2, spec="", preferName=False):
        scaled = value / self.factor
        rounded = trimzeroes(roundDecimal(scaled, accuracy))
        formattedValue = format(rounded, spec)

        if rounded == 0:
            return "0"

        single = abs(rounded) == 1
        if single:
            if self.name is not None:
                name = self.name
            else:
                name = self.namePlural
        else:
            if self.namePlural is not None:
                name = self.namePlural
            else:
                name = self.name

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

    def isUnit(self, u):
        return isinstance(u, str) and (u in self.names or u in self.symbols)

    def toUnitValue(self, v):
        return v * self.factor

    def __lt__(self, other):
        return self.factor < other.factor


# "Fixed" Unit: Formats to only the symbol.
class FixedUnit(Unit):
    """Unit that only formats to a single symbol"""

    def format(self, value, accuracy, spec, preferName=False):
        return self.symbol

    def toUnitValue(self, v):
        return self.factor


class FeetAndInchesUnit(Unit):
    """Unit for handling feet and inches"""

    def __init__(self, footsymbol, inchsymbol, factor):
        self.footsymbol = footsymbol
        self.inchsymbol = inchsymbol
        self.factor = factor

    def format(self, value, accuracy, spec, preferName=False):
        inchval = value / SV.inch                  # convert to inches
        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches
        roundedinchval = roundDecimal(inchval, accuracy)
        formatted = f"{trimzeroes(feetval)}{self.footsymbol}{trimzeroes(roundedinchval)}{self.inchsymbol}"
        return formatted

    def isUnit(self, u):
        return u == (self.footsymbol, self.inchsymbol)

    def toUnitValue(self, v):
        return None


class UnitRegistry():
    """Unit Registry"""

    def __init__(self, units):
        self._units = units

    def __getitem__(self, key):
        try:
            return next(unit for unit in self._units if unit.isUnit(key))
        except StopIteration:
            raise KeyError(key)

    def __getattr__(self, name):
        return self[name]

    def __contains__(self, name):
        return self[name] is not None


class SystemRegistry():
    """System Registry"""

    def __init__(self, units, unitnames):
        systemunits = [units[name] for name in unitnames]
        self._units = sorted(systemunits)

    # Try to find the best fitting unit, picking the largest unit if all units are too small
    def getBestUnit(self, value):
        value = abs(value)
        # Pair each unit with the unit following it
        for unit, nextunit in zip(self._units[:-1], self._units[1:]):
            # If we're smaller than the next unit's lowest value, then just use this unit
            if value < nextunit.factor:
                return unit
        # If we're too big for all the units, just use the biggest possible unit
        return self._units[-1]


class UnitValue(Decimal):
    """Unit Value"""

    def __format__(self, spec):
        value = Decimal(self)
        formatDict = parseSpec(spec)

        systems = formatDict["type"] or ""

        if all(s.casefold() in self._systems.keys() for s in systems):
            accuracy = formatDict["precision"] or 2
            accuracy = int(accuracy)
            formatDict["type"] = None
            formatDict["precision"] = None
            numspec = buildSpec(formatDict)

            formattedUnits = []
            for s in systems:
                preferName = s.upper() == s
                system = self._systems[s.casefold()]
                unit = system.getBestUnit(value)
                formattedUnits.append(unit.format(value, accuracy, numspec, preferName))

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
        value, unitStr = cls.getUnitValuePair(s)
        if value is None or unitStr is None:
            raise errors.InvalidSizeValue(s)
        value = Decimal(value)
        unit = cls._units[unitStr]
        if unit is None:
            raise errors.InvalidSizeValue(s)
        unitValue = unit.toUnitValue(value)
        return cls(unitValue)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)

    @classmethod
    def getUnitValuePair(cls, s):
        raise NotImplementedError


class SV(UnitValue):
    """Size Value (length)"""
    # Length Constants [meters]
    inch = Decimal("0.0254")
    foot = inch * Decimal("12")
    mile = foot * Decimal("5280")
    au = Decimal("1.495978707E+11")
    ly = mile * Decimal("5.879E+12")
    uniSV = Decimal("8.79848E+26")
    infinity = uniSV * Decimal("1E27")
    # SV units
    _units = UnitRegistry([
        Unit(symbol="ym", factor=Decimal("1e-24"), name="yoctometer", namePlural="yoctometers"),
        Unit(symbol="zm", factor=Decimal("1e-21"), name="zeptometer", namePlural="zeptometers"),
        Unit(symbol="am", factor=Decimal("1e-18"), name="attometer", namePlural="attometers"),
        Unit(symbol="fm", factor=Decimal("1e-15"), name="femtometer", namePlural="femtometers"),
        Unit(symbol="pm", factor=Decimal("1e-12"), name="picometer", namePlural="picometers"),
        Unit(symbol="nm", factor=Decimal("1e-9"), name="nanometer", namePlural="nanometers"),
        Unit(symbol="µm", factor=Decimal("1e-6"), name="micrometer", namePlural="micrometers", symbols=["um"]),
        Unit(symbol="mm", factor=Decimal("1e-3"), name="millimeter", namePlural="millimeters"),
        Unit(symbol="in", factor=inch, name="inche", namePlural="inches", symbols=["\""]),
        FeetAndInchesUnit("'", "\"", foot),
        Unit(symbol="cm", factor=Decimal("1e-2"), name="centimeter", namePlural="centimeters"),
        Unit(symbol="m", factor=Decimal("1e0"), name="meter", namePlural="meters"),
        Unit(symbol="km", factor=Decimal("1e3"), name="kilometer", namePlural="kilometers"),
        Unit(symbol="Mm", factor=Decimal("1e6"), name="megameter", namePlural="megameters"),
        Unit(symbol="Gm", factor=Decimal("1e9"), name="gigameter", namePlural="gigameters"),
        Unit(symbol="Tm", factor=Decimal("1e12"), name="terameter", namePlural="terameters"),
        Unit(symbol="Pm", factor=Decimal("1e15"), name="petameter", namePlural="petameters"),
        Unit(symbol="Em", factor=Decimal("1e18"), name="exameter", namePlural="exameters"),
        Unit(symbol="Zm", factor=Decimal("1e21"), name="zettameter", namePlural="zettameters"),
        Unit(symbol="Ym", factor=Decimal("1e24"), name="yottameter", namePlural="yottameters"),
        Unit(symbol="mi", factor=mile, name="mile", namePlural="miles"),
        Unit(symbol="ly", factor=ly, name="lightyear", namePlural="lightyears"),
        Unit(symbol="AU", factor=au, name="astronomical_unit", namePlural="astronomical_units"),
        Unit(symbol="uni", factor=uniSV * Decimal("1e0"), name="universe", namePlural="universes"),
        Unit(symbol="kuni", factor=uniSV * Decimal("1e3"), name="kilouniverse", namePlural="kilouniverses"),
        Unit(symbol="Muni", factor=uniSV * Decimal("1e6"), name="megauniverse", namePlural="megauniverses"),
        Unit(symbol="Guni", factor=uniSV * Decimal("1e9"), name="gigauniverse", namePlural="gigauniverses"),
        Unit(symbol="Tuni", factor=uniSV * Decimal("1e12"), name="terauniverse", namePlural="terauniverses"),
        Unit(symbol="Puni", factor=uniSV * Decimal("1e15"), name="petauniverse", namePlural="petauniverses"),
        Unit(symbol="Euni", factor=uniSV * Decimal("1e18"), name="exauniverse", namePlural="exauniverses"),
        Unit(symbol="Zuni", factor=uniSV * Decimal("1e21"), name="zettauniverse", namePlural="zettauniverses"),
        Unit(symbol="Yuni", factor=uniSV * Decimal("1e24"), name="yottauniverse", namePlural="yottauniverses"),
        FixedUnit(symbol="∞", factor=Decimal(infinity), names=["infinite", "infinity"]),
        Unit(factor=Decimal("0.0856"), name="credit card", namePlural="credit cards"),
        Unit(factor=Decimal("0.0856"), name="Natalie", namePlural="Natalies")
    ])
    # SV systems
    _systems = {
        "m": SystemRegistry(_units, [
            "ym",
            "zm",
            "am",
            "fm",
            "pm",
            "nm",
            "µm",
            "mm",
            "cm",
            "m",
            "km",
            "Mm",
            "Gm",
            "Tm",
            "Pm",
            "Em",
            "Zm",
            "Ym",
            "uni",
            "kuni",
            "Muni",
            "Guni",
            "Tuni",
            "Puni",
            "Euni",
            "Zuni",
            "Yuni",
            "∞"
        ]),
        "u": SystemRegistry(_units, [
            "ym",
            "zm",
            "am",
            "fm",
            "pm",
            "nm",
            "µm",
            "mm",
            "in",
            ("'", "\""),
            "mi",
            "AU",
            "ly",
            "uni",
            "kuni",
            "Muni",
            "Guni",
            "Tuni",
            "Puni",
            "Euni",
            "Zuni",
            "Yuni",
            "∞"
        ]),
        "o": SystemRegistry(_units, [
            "credit card",
            "Natalie"
        ])
    }

    @classmethod
    def getUnitValuePair(cls, s):
        s = removeBrackets(s)
        s = cls.isFeetAndInchesAndIfSoFixIt(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*) *(?P<unit>[a-zA-Z\'\"]+)", s)
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


class WV(UnitValue):
    """Weight Value (mass)"""
    # Weight Constants [grams]
    ounce = Decimal("28.35")
    pound = ounce * Decimal("16")
    uston = pound * Decimal("2000")
    earth = Decimal("5.9721986E+27")
    sun = Decimal("1.988435E+33")
    milkyway = Decimal("9.5E+43")
    uniWV = Decimal("3.4E+57")
    infinity = uniWV * Decimal("1E27")
    # WV units
    _units = UnitRegistry([
        Unit(symbol="yg", factor=Decimal("1e-24"), names=["yoctograms", "yoctograms"]),
        Unit(symbol="zg", factor=Decimal("1e-21"), names=["zeptograms", "zeptograms"]),
        Unit(symbol="ag", factor=Decimal("1e-18"), names=["attograms", "attogram"]),
        Unit(symbol="fg", factor=Decimal("1e-15"), names=["femtogram", "femtogram"]),
        Unit(symbol="pg", factor=Decimal("1e-12"), names=["picogram", "picogram"]),
        Unit(symbol="ng", factor=Decimal("1e-9"), names=["nanogram", "nanogram"]),
        Unit(symbol="µg", factor=Decimal("1e-6"), names=["microgram", "microgram"]),
        Unit(symbol="mg", factor=Decimal("1e-3"), names=["milligrams", "milligram"]),
        Unit(symbol="g", factor=Decimal("1e0"), names=["grams", "gram"]),
        Unit(symbol="oz", factor=ounce, names=["kilograms", "kilogram"]),
        Unit(symbol="lb", factor=pound, names=["pounds", "pound"], symbols=["lbs"]),
        Unit(symbol="kg", factor=Decimal("1e3"), names=["kilograms", "kilogram"]),
        Unit(symbol=" US tons", factor=uston),
        Unit(symbol="t", factor=Decimal("1e6"), names=["megagrams", "megagram", "ton", "tons", "tonnes", "tons"]),
        Unit(symbol="kt", factor=Decimal("1e9"), names=["gigagrams", "gigagram", "kilotons", "kiloton", "kilotonnes", "kilotonne"]),
        Unit(symbol="Mt", factor=Decimal("1e12"), names=["teragrams", "teragram", "megatons", "megaton", "megatonnes", "megatonne"]),
        Unit(symbol="Gt", factor=Decimal("1e15"), names=["petagrams", "petagram", "gigatons", "gigaton", "gigatonnes", "gigatonnes"]),
        Unit(symbol="Tt", factor=Decimal("1e18"), names=["exagrams", "exagram", "teratons", "teraton", "teratonnes", "teratonne"]),
        Unit(symbol="Pt", factor=Decimal("1e21"), names=["zettagrams", "zettagram", "petatons", "petaton", "petatonnes", "petatonne"]),
        Unit(symbol="Et", factor=Decimal("1e24"), names=["yottagrams", "yottagram", "exatons", "exaton", "exatonnes", "exatonne"]),
        Unit(symbol="Zt", factor=Decimal("1e27"), names=["zettatons", "zettaton", "zettatonnes", "zettatonne"]),
        Unit(symbol=" Earths", factor=earth, names=["earth", "earths"]),
        Unit(symbol="Yt", factor=Decimal("1e30"), names=["yottatons", "yottaton", "yottatonnes", "yottatonne"]),
        Unit(symbol=" Suns", factor=sun, names=["sun", "suns"]),
        Unit(symbol=" Milky Ways", factor=milkyway),
        Unit(symbol="uni", factor=uniWV * Decimal("1e0"), names=["universes", "universe"]),
        Unit(symbol="kuni", factor=uniWV * Decimal("1e3"), names=["kilouniverses", "kilouniverse"]),
        Unit(symbol="Muni", factor=uniWV * Decimal("1e6"), names=["megauniverses", "megauniverse"]),
        Unit(symbol="Guni", factor=uniWV * Decimal("1e9"), names=["gigauniverses", "gigauniverse"]),
        Unit(symbol="Tuni", factor=uniWV * Decimal("1e12"), names=["terauniverses", "terauniverse"]),
        Unit(symbol="Puni", factor=uniWV * Decimal("1e15"), names=["petauniverses", "petauniverse"]),
        Unit(symbol="Euni", factor=uniWV * Decimal("1e18"), names=["exauniverses", "exauniverse"]),
        Unit(symbol="Zuni", factor=uniWV * Decimal("1e21"), names=["zettauniverses", "zettauniverse"]),
        Unit(symbol="Yuni", factor=uniWV * Decimal("1e24"), names=["yottauniverses", "yottauniverse"]),
        FixedUnit(symbol="∞", factor=Decimal(infinity), names=["infinite", "infinity"])
    ])
    # WV systems
    _systems = {
        "m": SystemRegistry(_units, [
            "yg",
            "zg",
            "ag",
            "fg",
            "pg",
            "ng",
            "µg",
            "mg",
            "g",
            "kg",
            "t",
            "kt",
            "Mt",
            "Gt",
            "Tt",
            "Pt",
            "Et",
            "Zt",
            "Yt",
            "uni",
            "kuni",
            "Muni",
            "Guni",
            "Tuni",
            "Puni",
            "Euni",
            "Zuni",
            "Yuni",
            "∞",
        ]),
        "u": SystemRegistry(_units, [
            "yg",
            "zg",
            "ag",
            "fg",
            "pg",
            "ng",
            "µg",
            "mg",
            "g",
            "oz",
            "lb",
            " US tons",
            "earths",
            "sun",
            " Milky Ways",
            "uni",
            "kuni",
            "Muni",
            "Guni",
            "Tuni",
            "Puni",
            "Euni",
            "Zuni",
            "Yuni",
            "∞",
        ])
    }

    @classmethod
    def getUnitValuePair(cls, s):
        s = removeBrackets(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*) *(?P<unit>[a-zA-Z\'\"]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        return value, unit


class TV(UnitValue):
    """Time Value"""
    second = Decimal("1")
    minute = Decimal("60")
    hour = minute * Decimal("60")
    day = hour * Decimal("24")
    week = day * Decimal("7")
    month = day * Decimal("30")
    year = day * Decimal("365")
    _units = UnitRegistry([
        Unit(symbol="s", name="second", namePlural="seconds", factor=second, symbols=["sec"]),
        Unit(symbol="m", name="minute", namePlural="minutes", factor=minute, symbols=["min"]),
        Unit(symbol="h", name="hour", namePlural="hours", factor=hour, symbols=["hr"]),
        Unit(symbol="d", name="day", namePlural="days", factor=day, symbols=["dy"]),
        Unit(symbol="w", name="week", namePlural="weeks", factor=week, symbols=["wk"]),
        Unit(name="month", namePlural="", factor=month, names=["months"]),
        Unit(symbol="a", name="year", namePlural="years", factor=year, symbols=["y", "yr"])
    ])
    _systems = {
        "m": SystemRegistry(_units, [
            "seconds",
            "minutes",
            "hours",
            "days",
            "weeks",
            "months",
            "years"
        ])
    }

    @classmethod
    def getUnitValuePair(cls, s):
        s = removeBrackets(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z]+)", s)
        value, unit = None, None
        if match is not None:
            value, unit = match.group("value"), match.group("unit")
        if value is None:
            value = "1"
        return value, unit
