import re

from sizebot.digidecimal import Decimal, roundDecimal, roundDecimalHalf, trimzeroes
from sizebot import digierror as errors
from sizebot.utils import removeBrackets

# Unit constants
# Height [meters]
inch = Decimal("0.0254")
foot = inch * Decimal("12")
mile = foot * Decimal("5280")
ly = mile * Decimal("5879000000000")
au = Decimal("149597870700")
uniSV = Decimal("879848000000000000000000000")
infinitySV = uniSV * Decimal("1E27")
# Weight [grams]
ounce = Decimal("28.35")
pound = ounce * Decimal("16")
uston = pound * Decimal("2000")
earth = Decimal("5.9721986E+27")
sun = Decimal("1.988435E+33")
milkyway = Decimal("9.5E+43")
uniWV = Decimal("3.4E+57")
infinityWV = uniWV * Decimal("1E27")


# Unit: Formats a value by scaling it and applying the appropriate symbol suffix
class Unit():
    def __init__(self, symbol, factor, symbols=[], names=[]):
        self.symbol = symbol
        self.factor = factor
        self.symbols = symbols                          # case sensitive symbols
        self.names = [n.lower() for n in names]         # case insensitive names

    def format(self, value, accuracy):
        scaled = value / self.factor
        rounded = roundDecimal(scaled, accuracy)
        if rounded == 0:
            formatted = "0"
        else:
            formatted = f"{trimzeroes(rounded)}{self.symbol}"

        return formatted

    def isUnit(self, u):
        return isinstance(u, str) and (u.lower() in self.names or u == self.symbol or u in self.symbols)

    def toSV(self, v):
        return v * self.factor

    def __lt__(self, other):
        return self.factor < other.factor


# "Fixed" Unit: Formats to only the symbol.
class FixedUnit(Unit):
    def __init__(self, symbol, factor, symbols=[], names=[]):
        self.symbol = symbol
        self.factor = factor
        self.symbols = symbols                          # case sensitive symbols
        self.names = [n.lower() for n in names]         # case insensitive names

    def format(self, value, accuracy):
        return self.symbol

    def toSV(self, v):
        return self.factor


class FeetAndInchesUnit(Unit):
    def __init__(self, footsymbol, inchsymbol, factor):
        self.footsymbol = footsymbol
        self.inchsymbol = inchsymbol
        self.factor = factor

    def format(self, value, accuracy):
        inchval = value / inch                  # convert to inches
        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches
        roundedinchval = roundDecimal(inchval, accuracy)
        formatted = f"{trimzeroes(feetval)}{self.footsymbol}{trimzeroes(roundedinchval)}{self.inchsymbol}"
        return formatted

    def isUnit(self, u):
        return u == (self.footsymbol, self.inchsymbol)

    def toSV(self, v):
        return None


def getUnit(units, unitStr):
    for unit in units:
        if unit.isUnit(unitStr):
            return unit
    return None


# sorted list of units
svunits = [
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
    FixedUnit("∞", Decimal(infinitySV), names=["infinite", "infinity"])
]

wvunits = [
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
    Unit("Yt", Decimal("1e30"), names=["yottatons", "yottaton", "yottatonnes", "yottatonne"]),
    Unit(" Earths", earth, names=["earth", "earths"]),
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
    FixedUnit("∞", Decimal(infinityWV), names=["infinite", "infinity"])
]

svsystems = {
    "m": sorted([
        getUnit(svunits, "ym"),
        getUnit(svunits, "zm"),
        getUnit(svunits, "am"),
        getUnit(svunits, "fm"),
        getUnit(svunits, "pm"),
        getUnit(svunits, "nm"),
        getUnit(svunits, "µm"),
        getUnit(svunits, "mm"),
        getUnit(svunits, "cm"),
        getUnit(svunits, "m"),
        getUnit(svunits, "km"),
        getUnit(svunits, "Mm"),
        getUnit(svunits, "Gm"),
        getUnit(svunits, "Tm"),
        getUnit(svunits, "Pm"),
        getUnit(svunits, "Em"),
        getUnit(svunits, "Zm"),
        getUnit(svunits, "Ym"),
        getUnit(svunits, "uni"),
        getUnit(svunits, "kuni"),
        getUnit(svunits, "Muni"),
        getUnit(svunits, "Guni"),
        getUnit(svunits, "Tuni"),
        getUnit(svunits, "Puni"),
        getUnit(svunits, "Euni"),
        getUnit(svunits, "Zuni"),
        getUnit(svunits, "Yuni"),
        getUnit(svunits, "∞")
    ]),
    "u": sorted([
        getUnit(svunits, "ym"),
        getUnit(svunits, "zm"),
        getUnit(svunits, "am"),
        getUnit(svunits, "fm"),
        getUnit(svunits, "pm"),
        getUnit(svunits, "nm"),
        getUnit(svunits, "µm"),
        getUnit(svunits, "mm"),
        getUnit(svunits, "in"),
        getUnit(svunits, ("'", "\"")),
        getUnit(svunits, "mi"),
        getUnit(svunits, "AU"),
        getUnit(svunits, "ly"),
        getUnit(svunits, "uni"),
        getUnit(svunits, "kuni"),
        getUnit(svunits, "Muni"),
        getUnit(svunits, "Guni"),
        getUnit(svunits, "Tuni"),
        getUnit(svunits, "Puni"),
        getUnit(svunits, "Euni"),
        getUnit(svunits, "Zuni"),
        getUnit(svunits, "Yuni"),
        getUnit(svunits, "∞")
    ])
}

# sorted list of units
wvsystems = {
    "m": sorted([
        getUnit(wvunits, "yg"),
        getUnit(wvunits, "zg"),
        getUnit(wvunits, "ag"),
        getUnit(wvunits, "fg"),
        getUnit(wvunits, "pg"),
        getUnit(wvunits, "ng"),
        getUnit(wvunits, "µg"),
        getUnit(wvunits, "mg"),
        getUnit(wvunits, "g"),
        getUnit(wvunits, "kg"),
        getUnit(wvunits, "t"),
        getUnit(wvunits, "kt"),
        getUnit(wvunits, "Mt"),
        getUnit(wvunits, "Gt"),
        getUnit(wvunits, "Tt"),
        getUnit(wvunits, "Pt"),
        getUnit(wvunits, "Et"),
        getUnit(wvunits, "Zt"),
        getUnit(wvunits, "Yt"),
        getUnit(wvunits, "uni"),
        getUnit(wvunits, "kuni"),
        getUnit(wvunits, "Muni"),
        getUnit(wvunits, "Guni"),
        getUnit(wvunits, "Tuni"),
        getUnit(wvunits, "Puni"),
        getUnit(wvunits, "Euni"),
        getUnit(wvunits, "Zuni"),
        getUnit(wvunits, "Yuni"),
        getUnit(wvunits, "∞"),
    ]),
    "u": sorted([
        getUnit(wvunits, "yg"),
        getUnit(wvunits, "zg"),
        getUnit(wvunits, "ag"),
        getUnit(wvunits, "fg"),
        getUnit(wvunits, "pg"),
        getUnit(wvunits, "ng"),
        getUnit(wvunits, "µg"),
        getUnit(wvunits, "mg"),
        getUnit(wvunits, "g"),
        getUnit(wvunits, "oz"),
        getUnit(wvunits, "lb"),
        getUnit(wvunits, " US tons"),
        getUnit(wvunits, "earths"),
        getUnit(wvunits, "sun"),
        getUnit(wvunits, " Milky Ways"),
        getUnit(wvunits, "uni"),
        getUnit(wvunits, "kuni"),
        getUnit(wvunits, "Muni"),
        getUnit(wvunits, "Guni"),
        getUnit(wvunits, "Tuni"),
        getUnit(wvunits, "Puni"),
        getUnit(wvunits, "Euni"),
        getUnit(wvunits, "Zuni"),
        getUnit(wvunits, "Yuni"),
        getUnit(wvunits, "∞"),
    ])
}


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

    valueSV = tryOrNone(toSV, multOrSvStr)
    valueMult = None
    if valueSV is None:
        valueMult = tryOrNone(toMult, multOrSvStr)
    if valueSV is None and valueMult is None:
        raise errors.InvalidSizeValue(s)
    if valueSV and isSub:
        valueSV = -valueSV

    valueTV = tryOrNone(toTV, tvStr)
    if valueTV is None:
        raise errors.InvalidSizeValue(s)

    stopSV = None
    stopTV = None
    if stopStr is not None:
        stopSV = tryOrNone(toSV, stopStr)
        if stopSV is None:
            stopTV = tryOrNone(toTV, stopStr)
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


# Get letters from string
def getTVPair(s):
    s = removeBrackets(s)
    match = re.search(r"(?P<value>[\-+]?\d+\.?\d*)? *(?P<unit>[a-zA-Z\'\"]+)", s)
    value = None
    unit = None
    if match is not None:
        value = match.group("value")
        unit = match.group("unit")
    return value, unit


def toTV(s):
    value, unit = getTVPair(s)
    if unit is None:
        raise errors.InvalidSizeValue(s)
    if value is None:
        value = Decimal("1")
    unitlower = unit.lower()
    value = Decimal(value)
    if unitlower in ["second", "seconds", "sec"] or unit == "s":
        scale = Decimal("1E0")
    elif unitlower in ["minute", "minutes", "min"] or unit == "m":
        scale = Decimal("60")
    elif unitlower in ["hour", "hours", "hr"] or unit == "h":
        scale = Decimal("3600")
    elif unitlower in ["day", "days", "dy"] or unit == "d":
        scale = Decimal("3600") * Decimal("24")
    elif unitlower in ["week", "weeks", "wk"] or unit == "w":
        scale = Decimal("3600") * Decimal("24") * Decimal("7")
    elif unitlower in ["month", "months"]:
        scale = Decimal("3600") * Decimal("24") * Decimal("30")
    elif unitlower in ["year", "years", "yr"] or unit in ["y", "a"]:
        scale = Decimal("3600") * Decimal("24") * Decimal("365")
    else:
        raise errors.InvalidSizeValue(s)
    return value * scale


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


def isFeetAndInchesAndIfSoFixIt(value):
    regex = r"^((?P<feet>\d+\.?\d*)(ft|foot|feet|'))?((?P<inch>\d+\.?\d*)(in|\"))?"
    m = re.match(regex, value, flags = re.I)
    if not m:
        return value
    feetval = m.group("feet")
    inchval = m.group("inch")
    if feetval is None and inchval is None:
        return value
    if feetval is None:
        feetval = "0"
    if inchval is None:
        inchval = "0"
    totalinches = (Decimal(feetval) * Decimal("12")) + Decimal(inchval)
    return f"{totalinches}in"


# Get letters from string
def getSVPair(s):
    s = removeBrackets(s)
    s = isFeetAndInchesAndIfSoFixIt(s)
    match = re.search(r"(?P<value>[\-+]?\d+\.?\d*) *(?P<unit>[a-zA-Z\'\"]+)", s)
    value, unit = None, None
    if match is not None:
        value, unit = match.group("value"), match.group("unit")
    return value, unit


# Convert any supported height to "size value"
def toSV(s):
    value, unitStr = getSVPair(s)
    if value is None or unitStr is None:
        raise errors.InvalidSizeValue(s)
    value = Decimal(value)
    unit = getUnit(svunits, unitStr)
    if unit is None:
        raise errors.InvalidSizeValue(s)
    valueSV = unit.toSV(value)
    return valueSV


# Convert any supported weight to "weight value", or milligrams
def toWV(s):
    value, unitStr = getSVPair(s)
    if value is None or unitStr is None:
        raise errors.InvalidSizeValue(s)
    value = Decimal(value)
    unit = getUnit(wvunits, unitStr)
    if unit is None:
        raise errors.InvalidSizeValue(s)
    valueWV = unit.toSV(value)
    return valueWV


# Try to find the best fitting unit, picking the largest unit if all units are too small
def getBestUnit(value, units):
    # Pair each unit with the unit following it
    for unit, nextunit in zip(units[:-1], units[1:]):
        # If we're smaller than the next unit's lowest value, then just use this unit
        if value < nextunit.factor:
            return unit
    # If we're too big for all the units, just use the biggest possible unit
    return units[-1]


# Convert "size values" to a more readable format.
def fromSV(value, system = "m", accuracy = 2):
    if system not in svsystems.keys():
        raise errors.InvalidUnitSystemException(system)
    unit = getBestUnit(abs(value), svsystems[system])
    formatted = unit.format(value, accuracy)
    return formatted


# Convert "weight values" to a more readable format.
def fromWV(value, system = "m", accuracy = 2):
    if system not in wvsystems.keys():
        raise errors.InvalidUnitSystemException(system)
    unit = getBestUnit(abs(value), wvsystems[system])
    formatted = unit.format(value, accuracy)
    return formatted


def toShoeSize(inchval):
    child = False
    shoesize = Decimal("3") * inchval
    shoesize = shoesize - Decimal("22")
    if shoesize < Decimal("1"):
        child = True
        shoesize += Decimal("12") + Decimal("1") / Decimal("3")
    if shoesize < Decimal("1"):
        return "No shoes exist this small!"
    shoesize = roundDecimalHalf(shoesize)
    prefix = "Size US"
    if child:
        prefix += " Children's"
    return f"{prefix} {shoesize:,}"


def getShoePair(s):
    match = re.search(r"(\d+\.?\d*) *[a-zA-Z]?", s)
    shoesize, suffix = None, None
    if match is not None:
        shoesize, suffix = match.group(1), match.group(2)
    # TODO: Raise an error here
    return shoesize, suffix


# Currently unused
def fromShoeSize(shoestring):
    shoesize, suffix = getShoePair(shoestring)
    if shoesize is None:
        return None
        # TODO: Raise an error in getShowPair
    child = "c" in suffix.toLower()
    shoesize = Decimal(shoesize)
    shoeinches = shoesize + Decimal("22")
    if child:
        shoeinches -= (Decimal("12") + (Decimal("1") / Decimal("3")))
    shoeinches /= Decimal("3")
    shoesv = shoeinches * inch
    return shoesv
