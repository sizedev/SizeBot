import re

from sizebot.digidecimal import Decimal, roundDecimal, trimzeroes
from sizebot import digierror as errors
from sizebot.utils import removeBrackets


def tryOrNone(fn, val):
    try:
        result = fn(val)
    except errors.InvalidSizeValue:
        result = None
    return result


re_num = "\\d+\\.?\\d*"
re_num_unit = f"{re_num} *[A-Za-z]+"
re_opnum_unit = f"({re_num})? *[A-Za-z]+"


rateDividers = "|".join(re.escape(d) for d in ("/", "per", "every"))
stopDividers = "|".join(re.escape(d) for d in ("until", "for", "->"))
addPrefixes = ["+", "plus", "add"]
subPrefixes = ["-", "minus", "subtract", "sub"]
addSubPrefixes = "|".join(re.escape(d) for d in addPrefixes + subPrefixes)
re_rate = re.compile(f"(?P<prefix>{addSubPrefixes})? *(?P<multOrSv>.*) *({rateDividers}) *(?P<tv>{re_opnum_unit}) *(({stopDividers}) *(?P<stop>{re_opnum_unit}))?")


def toRate(s):
    match = re_rate.match(s)
    if match is None:
        raise errors.InvalidSizeValue(s)
    prefix = match.group("prefix")
    multOrSvStr = match.group("multOrSv")
    tvStr = match.group("tv")
    stopStr = match.group("stop")

    isSub = prefix in subPrefixes

    valueSV = tryOrNone(SV.parse, multOrSvStr)
    valueMult = None
    if valueSV is None:
        valueMult = tryOrNone(toMult, multOrSvStr)
    if valueSV is None and valueMult is None:
        raise errors.InvalidSizeValue(s)
    if valueSV and isSub:
        valueSV = -valueSV

    valueTV = tryOrNone(TV.parse, tvStr)
    if valueTV is None:
        raise errors.InvalidSizeValue(s)

    stopSV = None
    stopTV = None
    if stopStr is not None:
        stopSV = tryOrNone(SV.parse, stopStr)
        if stopSV is None:
            stopTV = tryOrNone(TV.parse, stopStr)
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


multPrefixes = ["x", "X", "*", "times", "mult", "multiply"]
divPrefixes = ["/", "÷", "div", "divide"]
prefixes = '|'.join(re.escape(p) for p in multPrefixes + divPrefixes)
suffixes = '|'.join(re.escape(p) for p in ["x", "X"])
re_mult = re.compile(f"(?P<prefix>{prefixes})? *(?P<multValue>{re_num}) *(?P<suffix>{suffixes})?")


def toMult(s):
    match = re_mult.match(s)
    if match is None:
        raise errors.InvalidSizeValue(s)
    prefix = match.group("prefix") or match.group("suffix")
    multValue = Decimal(match.group("multValue"))

    isDivide = prefix in divPrefixes
    if isDivide:
        multValue = 1 / multValue

    return multValue


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
(?P<type>[a-zA-Z%])?
\Z
""", re.VERBOSE)


def parseSpec(spec):
    m = formatSpecRe.match(spec)
    if m is None:
        raise ValueError("Invalid format specifier: " + spec)
    return m.groupdict()


def buildSpec(formatDict):
    spec = ""
    if formatDict["align"] is not None:
        if formatDict["fill"] is not None:
            spec += formatDict["fill"]
        spec += formatDict["align"]
    if formatDict["sign"] is not None:
        spec += formatDict["sign"]
    if formatDict["zeropad"] is not None:
        spec += formatDict["zeropad"]
    if formatDict["minimumwidth"] is not None:
        spec += formatDict["minimumwidth"]
    if formatDict["thousands_sep"] is not None:
        spec += formatDict["thousands_sep"]
    if formatDict["precision"] is not None:
        spec += "." + formatDict["precision"]
    if formatDict["type"] is not None:
        spec += "." + formatDict["type"]
    return spec


# Unit: Formats a value by scaling it and applying the appropriate symbol suffix
class Unit():
    def __init__(self, symbol, factor, symbols=[], names=[]):
        self.symbol = symbol
        self.factor = factor
        self.symbols = symbols                          # case sensitive symbols
        self.names = [n.lower() for n in names]         # case insensitive names

    def format(self, value, accuracy=2, spec=""):
        scaled = value / self.factor
        rounded = trimzeroes(roundDecimal(scaled, accuracy))
        if rounded == 0:
            formatted = "0"
        else:
            formatted = f"{format(rounded, spec)}{self.symbol}"

        return formatted

    def isUnit(self, u):
        return isinstance(u, str) and (u.lower() in self.names or u == self.symbol or u in self.symbols)

    def toUnitValue(self, v):
        return v * self.factor

    def __lt__(self, other):
        return self.factor < other.factor


# "Fixed" Unit: Formats to only the symbol.
class FixedUnit(Unit):
    def format(self, value, accuracy, spec):
        return self.symbol

    def toUnitValue(self, v):
        return self.factor


class FeetAndInchesUnit(Unit):
    def __init__(self, footsymbol, inchsymbol, factor):
        self.footsymbol = footsymbol
        self.inchsymbol = inchsymbol
        self.factor = factor

    def format(self, value, accuracy, spec):
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
    def __init__(self, units):
        self._units = units

    def __getitem__(self, key):
        try:
            return next(unit for unit in self._units if unit.isUnit(key))
        except StopIteration:
            return None

    def __getattr__(self, name):
        return self[name]

    def __contains__(self, name):
        return self[name] is not None


class SystemRegistry():
    def __init__(self, units, unitnames):
        self._units = sorted(units[name] for name in unitnames)

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
    def __format__(self, spec):
        value = Decimal(self)
        formatDict = parseSpec(spec)

        system = formatDict["type"]

        if system in self._systems.keys():
            accuracy = formatDict["precision"] or 2
            accuracy = int(accuracy)
            formatDict["type"] = None
            formatDict["precision"] = None
            numspec = buildSpec(formatDict)

            unit = self._systems[system].getBestUnit(value)
            formatted = unit.format(value, accuracy, numspec)
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
        Unit("ym", Decimal("1e-24"), names=["yoctometers", "yoctometer"]),
        Unit("zm", Decimal("1e-21"), names=["zeptometers", "zeptometer"]),
        Unit("am", Decimal("1e-18"), names=["attometers", "attometer"]),
        Unit("fm", Decimal("1e-15"), names=["femtometers", "femtometer"]),
        Unit("pm", Decimal("1e-12"), names=["picometers", "picometer"]),
        Unit("nm", Decimal("1e-9"), names=["nanometers", "nanometer"]),
        Unit("µm", Decimal("1e-6"), names=["micrometers", "micrometer"], symbols=["um"]),
        Unit("mm", Decimal("1e-3"), names=["millimeters", "millimeter"]),
        Unit("in", inch, names=["inches", "inch", "in", "\""]),
        FeetAndInchesUnit("'", "\"", foot),
        Unit("cm", Decimal("1e-2"), names=["centimeters", "centimeter"]),
        Unit("m", Decimal("1e0"), names=["meters", "meter"]),
        Unit("km", Decimal("1e3"), names=["kilometers", "kilometer"]),
        Unit("Mm", Decimal("1e6"), names=["megameters", "megameter"]),
        Unit("Gm", Decimal("1e9"), names=["gigameters", "gigameter"]),
        Unit("Tm", Decimal("1e12"), names=["terameters", "terameter"]),
        Unit("Pm", Decimal("1e15"), names=["petameters", "petameter"]),
        Unit("Em", Decimal("1e18"), names=["exameters", "exameter"]),
        Unit("Zm", Decimal("1e21"), names=["zettameters", "zettameter"]),
        Unit("Ym", Decimal("1e24"), names=["yottameters", "yottameter"]),
        Unit("mi", mile, names=["miles", "mile"]),
        Unit("ly", ly, names=["lightyears", "lightyear"]),
        Unit("AU", au, names=["astronomical_units", "astronomical_unit"]),
        Unit("uni", uniSV * Decimal("1e0"), names=["universes", "universe"]),
        Unit("kuni", uniSV * Decimal("1e3"), names=["kilouniverses", "kilouniverse"]),
        Unit("Muni", uniSV * Decimal("1e6"), names=["megauniverses", "megauniverse"]),
        Unit("Guni", uniSV * Decimal("1e9"), names=["gigauniverses", "gigauniverse"]),
        Unit("Tuni", uniSV * Decimal("1e12"), names=["terauniverses", "terauniverse"]),
        Unit("Puni", uniSV * Decimal("1e15"), names=["petauniverses", "petauniverse"]),
        Unit("Euni", uniSV * Decimal("1e18"), names=["exauniverses", "exauniverse"]),
        Unit("Zuni", uniSV * Decimal("1e21"), names=["zettauniverses", "zettauniverse"]),
        Unit("Yuni", uniSV * Decimal("1e24"), names=["yottauniverses", "yottauniverse"]),
        FixedUnit("∞", Decimal(infinity), names=["infinite", "infinity"])
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
        Unit("yg", Decimal("1e-24"), names=["yoctograms", "yoctograms"]),
        Unit("zg", Decimal("1e-21"), names=["zeptograms", "zeptograms"]),
        Unit("ag", Decimal("1e-18"), names=["attograms", "attogram"]),
        Unit("fg", Decimal("1e-15"), names=["femtogram", "femtogram"]),
        Unit("pg", Decimal("1e-12"), names=["picogram", "picogram"]),
        Unit("ng", Decimal("1e-9"), names=["nanogram", "nanogram"]),
        Unit("µg", Decimal("1e-6"), names=["microgram", "microgram"]),
        Unit("mg", Decimal("1e-3"), names=["milligrams", "milligram"]),
        Unit("g", Decimal("1e0"), names=["grams", "gram"]),
        Unit("oz", ounce, names=["kilograms", "kilogram"]),
        Unit("lb", pound, names=["pounds", "pound"], symbols=["lbs"]),
        Unit("kg", Decimal("1e3"), names=["kilograms", "kilogram"]),
        Unit(" US tons", uston),
        Unit("t", Decimal("1e6"), names=["megagrams", "megagram", "ton", "tons", "tonnes", "tons"]),
        Unit("kt", Decimal("1e9"), names=["gigagrams", "gigagram", "kilotons", "kiloton", "kilotonnes", "kilotonne"]),
        Unit("Mt", Decimal("1e12"), names=["teragrams", "teragram", "megatons", "megaton", "megatonnes", "megatonne"]),
        Unit("Gt", Decimal("1e15"), names=["petagrams", "petagram", "gigatons", "gigaton", "gigatonnes", "gigatonnes"]),
        Unit("Tt", Decimal("1e18"), names=["exagrams", "exagram", "teratons", "teraton", "teratonnes", "teratonne"]),
        Unit("Pt", Decimal("1e21"), names=["zettagrams", "zettagram", "petatons", "petaton", "petatonnes", "petatonne"]),
        Unit("Et", Decimal("1e24"), names=["yottagrams", "yottagram", "exatons", "exaton", "exatonnes", "exatonne"]),
        Unit("Zt", Decimal("1e27"), names=["zettatons", "zettaton", "zettatonnes", "zettatonne"]),
        Unit(" Earths", earth, names=["earth", "earths"]),
        Unit("Yt", Decimal("1e30"), names=["yottatons", "yottaton", "yottatonnes", "yottatonne"]),
        Unit(" Suns", sun, names=["sun", "suns"]),
        Unit(" Milky Ways", milkyway),
        Unit("uni", uniWV * Decimal("1e0"), names=["universes", "universe"]),
        Unit("kuni", uniWV * Decimal("1e3"), names=["kilouniverses", "kilouniverse"]),
        Unit("Muni", uniWV * Decimal("1e6"), names=["megauniverses", "megauniverse"]),
        Unit("Guni", uniWV * Decimal("1e9"), names=["gigauniverses", "gigauniverse"]),
        Unit("Tuni", uniWV * Decimal("1e12"), names=["terauniverses", "terauniverse"]),
        Unit("Puni", uniWV * Decimal("1e15"), names=["petauniverses", "petauniverse"]),
        Unit("Euni", uniWV * Decimal("1e18"), names=["exauniverses", "exauniverse"]),
        Unit("Zuni", uniWV * Decimal("1e21"), names=["zettauniverses", "zettauniverse"]),
        Unit("Yuni", uniWV * Decimal("1e24"), names=["yottauniverses", "yottauniverse"]),
        FixedUnit("∞", Decimal(infinity), names=["infinite", "infinity"])
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
    second = Decimal("1")
    minute = Decimal("60")
    hour = minute * Decimal("60")
    day = hour * Decimal("24")
    week = day * Decimal("7")
    month = day * Decimal("30")
    year = day * Decimal("365")
    _units = UnitRegistry([
        Unit("s", second, names=["second", "seconds", "sec"]),
        Unit("m", minute, names=["minute", "minutes", "min"]),
        Unit("h", hour, names=["hour", "hours", "hr"]),
        Unit("d", day, names=["day", "days", "dy"]),
        Unit("w", week, names=["week", "weeks", "wk"]),
        Unit(None, month, names=["month", "months"]),
        Unit("a", year, names=["year", "years", "yr"], symbols=["y"])
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
