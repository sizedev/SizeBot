import re

from discord.ext import commands

from sizebot.digidecimal import Decimal
from sizebot import digierror as errors

# Unit constants
# Height [meters]
inch = Decimal("0.0254")
foot = inch * Decimal("12")
mile = foot * Decimal("5280")
ly = mile * Decimal("5879000000000")
au = Decimal("149597870700")
uni = Decimal("879848000000000000000000000")
infinity = uni * Decimal("1e27")
# Weight [grams]
ounce = Decimal("28.35")
pound = ounce * Decimal("16")
uston = pound * Decimal("2000")
earth = Decimal("5972198600000000000000000000")
sun = Decimal("1988435000000000000000000000000000")
milkyway = Decimal("95000000000000000000000000000000000000000000")
uniw = Decimal("3400000000000000000000000000000000000000000000000000000000")


# Format a Decimal to a string, removing exponents and trailing zeroes after the decimal
def formatDecimal(d):
    # `normalize()` removes ALL trailing zeroes, including ones before the decimal place
    # `+ 0` readds the trailing zeroes before the decimal place, if necessary
    return str(d.normalize() + 0)


def roundDecimal(d, accuracy = 0):
    places = Decimal("10") ** -accuracy
    return d.quantize(places)


def roundDecimalHalf(number):
    return roundDecimal(number * Decimal("2")) / Decimal("2")


def removeBrackets(s):
    s = re.sub(r"[\[\]<>]", "", s)
    return s


dividers = "|".join(["/", "per", "every"])
re_rate = re.compile(f"(P<multOrSv>.*) *({dividers}) *(P<Tv>.*)")


def toRate(s):
    match = re.match(s)
    if match is None:
        raise errors.InvalidRateValue(s)
    multOrSvStr = match.groups("multOrSv")
    tvStr = match.groups("Tv")
    try:
        valueTV = toTV(tvStr)
    except errors.InvalidSizeValue:
        raise errors.InvalidSizeValue(s)

    try:
        valueSV = toSV(multOrSvStr)
    except errors.InvalidSizeValue:
        valueSV = None

    valueMult = None
    if valueSV is None:
        try:
            valueMult = toMult(multOrSvStr)
        except errors.InvalidSizeValue:
            raise errors.InvalidSizeValue(s)

    return valueSV, valueMult, valueTV


# Get letters from string
def getTVPair(s):
    s = removeBrackets(s)
    match = re.search(r"(\d+\.?\d*) *([a-zA-Z]+)", s)
    value, unit = None, None
    if match is not None:
        value, unit = match.group(1), match.group(2)
    return value, unit


def toTV(s):
    value, unit = getTVPair(s)
    if value is None or unit is None:
        raise errors.InvalidSizeValue(s)
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
    return value / scale


def toMult(s):
    pass


# Get letters from string
def getSVPair(s):
    s = removeBrackets(s)
    s = isFeetAndInchesAndIfSoFixIt(s)
    match = re.search(r"(\d+\.?\d*) *([a-zA-Z\'\"]+)", s)
    value, unit = None, None
    if match is not None:
        value, unit = match.group(1), match.group(2)
    return value, unit


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


# Convert any supported height to "size value"
def toSV(s):
    value, unit = getSVPair(s)
    if value is None or unit is None:
        raise errors.InvalidSizeValue(s)
    unitlower = unit.lower()
    if unitlower in ["yoctometers", "yoctometer"] or unit == "ym":
        output = Decimal(value) / Decimal("1e24")
    elif unitlower in ["zeptometers", "zeptometer"] or unit == "zm":
        output = Decimal(value) / Decimal("1e21")
    elif unitlower in ["attometers", "attometer"] or unit == "am":
        output = Decimal(value) / Decimal("1e18")
    elif unitlower in ["femtometers", "femtometer"] or unit == "fm":
        output = Decimal(value) / Decimal("1e15")
    elif unitlower in ["picometers", "picometer"] or unit == "pm":
        output = Decimal(value) / Decimal("1e12")
    elif unitlower in ["nanometers", "nanometer"] or unit == "nm":
        output = Decimal(value) / Decimal("1e9")
    elif unitlower in ["micrometers", "micrometer"] or unit in ["um", "µm"]:
        output = Decimal(value) / Decimal("1e6")
    elif unitlower in ["millimeters", "millimeter"] or unit == "mm":
        output = Decimal(value) / Decimal("1e3")
    elif unitlower in ["centimeters", "centimeter"] or unit == "cm":
        output = Decimal(value) / Decimal("1e2")
    elif unitlower in ["meters", "meter"] or unit == "m":
        output = Decimal(value)
    elif unitlower in ["kilometers", "kilometer"] or unit == "km":
        output = Decimal(value) * Decimal("1e3")
    elif unitlower in ["megameters", "megameter"] or unit == "Mm":
        output = Decimal(value) * Decimal("1e6")
    elif unitlower in ["gigameters", "gigameter"] or unit == "Gm":
        output = Decimal(value) * Decimal("1e9")
    elif unitlower in ["terameters", "terameter"] or unit == "Tm":
        output = Decimal(value) * Decimal("1e12")
    elif unitlower in ["petameters", "petameter"] or unit == "Pm":
        output = Decimal(value) * Decimal("1e15")
    elif unitlower in ["exameters", "exameter"] or unit == "Mm":
        output = Decimal(value) * Decimal("1e18")
    elif unitlower in ["zettameters", "zettameter"] or unit == "Zm":
        output = Decimal(value) * Decimal("1e21")
    elif unitlower in ["yottameters", "yottameter"] or unit == "Ym":
        output = Decimal(value) * Decimal("1e24")
    elif unitlower in ["inches", "inch", "in", "\""]:
        output = Decimal(value) * inch
    elif unitlower in ["feet", "foot", "ft", "'"]:
        output = Decimal(value) * foot
    elif unitlower in ["miles", "mile"] or unit == "mi":
        output = Decimal(value) * mile
    elif unitlower in ["lightyears", "lightyear"] or unit == "ly":
        output = Decimal(value) * ly
    elif unitlower in ["astronomical_units", "astronomical_unit"] or unit == "AU":
        output = Decimal(value) * au
    elif unitlower in ["universes", "universe"] or unit == "uni":
        output = Decimal(value) * uni
    elif unitlower in ["kilouniverses", "kilouniverse"] or unit == "kuni":
        output = Decimal(value) * uni * Decimal("1e3")
    elif unitlower in ["megauniverses", "megauniverse"] or unit == "Muni":
        output = Decimal(value) * uni * Decimal("1e6")
    elif unitlower in ["gigauniverses", "gigauniverse"] or unit == "Guni":
        output = Decimal(value) * uni * Decimal("1e9")
    elif unitlower in ["terauniverses", "terauniverse"] or unit == "Tuni":
        output = Decimal(value) * uni * Decimal("1e12")
    elif unitlower in ["petauniverses", "petauniverse"] or unit == "Puni":
        output = Decimal(value) * uni * Decimal("1e15")
    elif unitlower in ["exauniverses", "exauniverse"] or unit == "Euni":
        output = Decimal(value) * uni * Decimal("1e18")
    elif unitlower in ["zettauniverses", "zettauniverse"] or unit == "Zuni":
        output = Decimal(value) * uni * Decimal("1e21")
    elif unitlower in ["yottauniverses", "yottauniverse"] or unit == "Yuni":
        output = Decimal(value) * uni * Decimal("1e24")
    else:
        raise errors.InvalidSizeValue(s)
    return output


# Convert any supported weight to "weight value", or milligrams.
def toWV(s):
    value, unit = getSVPair(s)
    if value is None or unit is None:
        raise errors.InvalidSizeValue(s)
    unitlower = unit.lower()
    if unitlower in ["yoctograms", "yoctograms"] or unit == "yg":
        output = Decimal(value) / Decimal("1e24")
    elif unitlower in ["zeptograms", "zeptograms"] or unit == "zg":
        output = Decimal(value) / Decimal("1e21")
    elif unitlower in ["attograms", "attogram"] or unit == "ag":
        output = Decimal(value) / Decimal("1e18")
    elif unitlower in ["femtogram", "femtogram"] or unit == "fg":
        output = Decimal(value) / Decimal("1e15")
    elif unitlower in ["picogram", "picogram"] or unit == "pg":
        output = Decimal(value) / Decimal("1e12")
    elif unitlower in ["nanogram", "nanogram"] or unit == "ng":
        output = Decimal(value) / Decimal("1e9")
    elif unitlower in ["microgram", "microgram"] or unit == "ug":
        output = Decimal(value) / Decimal("1e6")
    elif unitlower in ["milligrams", "milligram"] or unit == "mg":
        output = Decimal(value)
    elif unitlower in ["grams", "gram"] or unit == "g":
        output = Decimal(value) * Decimal("1e3")
    elif unitlower in ["kilograms", "kilogram"] or unit == "kg":
        output = Decimal(value) * Decimal("1e6")
    elif unitlower in ["megagrams", "megagram", "ton", "tons", "tonnes", "tons"] or unit == ["t", "Mg"]:
        output = Decimal(value) * Decimal("1e9")
    elif unitlower in ["gigagrams", "gigagram", "kilotons", "kiloton", "kilotonnes", "kilotonne"] or unit in ["kt", "Gg"]:
        output = Decimal(value) * Decimal("1e12")
    elif unitlower in ["teragrams", "teragram", "megatons", "megaton", "megatonnes", "megatonne"] or unit in ["Mt", "Tg"]:
        output = Decimal(value) * Decimal("1e15")
    elif unitlower in ["petagrams", "petagram", "gigatons", "gigaton", "gigatonnes", "gigatonnes"] or unit in ["Gt", "Pg"]:
        output = Decimal(value) * Decimal("1e18")
    elif unitlower in ["exagrams", "exagram", "teratons", "teraton", "teratonnes", "teratonne"] or unit in ["Tt", "Eg"]:
        output = Decimal(value) * Decimal("1e21")
    elif unitlower in ["zettagrams", "zettagram", "petatons", "petaton", "petatonnes", "petatonne"] or unit in ["Pt", "Zg"]:
        output = Decimal(value) * Decimal("1e24")
    elif unitlower in ["yottagrams", "yottagram", "exatons", "exaton", "exatonnes", "exatonne"] or unit == ["Et", "Yg"]:
        output = Decimal(value) * Decimal("1e27")
    elif unitlower in ["zettatons", "zettaton", "zettatonnes", "zettatonne"] or unit == "Zt":
        output = Decimal(value) * Decimal("1e30")
    elif unitlower in ["yottatons", "yottaton", "yottatonnes", "yottatonne"] or unit == "Yt":
        output = Decimal(value) * Decimal("1e33")
    elif unitlower in ["universes", "universe"] or unit == "uni":
        output = Decimal(value) * uniw
    elif unitlower in ["kilouniverses", "kilouniverse"] or unit == "kuni":
        output = Decimal(value) * uniw * Decimal("1e3")
    elif unitlower in ["megauniverses", "megauniverse"] or unit == "Muni":
        output = Decimal(value) * uniw * Decimal("1e6")
    elif unitlower in ["gigauniverses", "gigauniverse"] or unit == "Guni":
        output = Decimal(value) * uniw * Decimal("1e9")
    elif unitlower in ["terauniverses", "terauniverse"] or unit == "Tuni":
        output = Decimal(value) * uniw * Decimal("1e12")
    elif unitlower in ["petauniverses", "petauniverse"] or unit == "Puni":
        output = Decimal(value) * uniw * Decimal("1e15")
    elif unitlower in ["exauniverses", "exauniverse"] or unit == "Euni":
        output = Decimal(value) * uniw * Decimal("1e18")
    elif unitlower in ["zettauniverses", "zettauniverse"] or unit == "Zuni":
        output = Decimal(value) * uniw * Decimal("1e21")
    elif unitlower in ["yottauniverses", "yottauniverse"] or unit == "Yuni":
        output = Decimal(value) * uniw * Decimal("1e24")
    elif unitlower in ["ounces", "ounce"] or unit == "oz":
        output = Decimal(value) * ounce
    elif unitlower in ["pounds", "pound"] or unit in ["lb", "lbs"]:
        output = Decimal(value) * pound
    elif unitlower in ["earth", "earths"]:
        output = Decimal(value) * earth
    elif unitlower in ["sun", "suns"]:
        output = Decimal(value) * sun
    else:
        raise errors.InvalidSizeValue(s)
    return output


# Unit: Formats a value by scaling it and applying the appropriate symbol suffix
class Unit():
    def __init__(self, symbol, factor):
        self.symbol = symbol
        self.factor = factor

    def format(self, value, accuracy):
        scaled = value / self.factor
        rounded = roundDecimal(scaled, accuracy)
        if rounded <= 0:
            formatted = "0"
        else:
            formatted = formatDecimal(rounded) + self.symbol

        return formatted


# "Fixed" Unit: Formats to only the symbol.
class FixedUnit(Unit):
    def __init__(self, symbol, factor):
        self.symbol = symbol
        self.factor = factor

    def format(self, value, accuracy):
        return self.symbol


class FeetAndInchesUnit(Unit):
    def __init__(self, footsymbol, inchsymbol, factor):
        self.footsymbol = footsymbol
        self.inchsymbol = inchsymbol
        self.factor = factor

    def format(self, value, accuracy):
        inchval = value / inch                  # convert to inches
        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches
        roundedinchval = roundDecimal(inchval, accuracy)
        formatted = formatDecimal(feetval) + self.footsymbol + formatDecimal(roundedinchval) + self.inchsymbol
        return formatted


# sorted list of units
svunits = {
    "m": sorted([
        Unit("ym", Decimal("1e-24")),
        Unit("zm", Decimal("1e-21")),
        Unit("am", Decimal("1e-18")),
        Unit("fm", Decimal("1e-15")),
        Unit("pm", Decimal("1e-12")),
        Unit("nm", Decimal("1e-9")),
        Unit("µm", Decimal("1e-6")),
        Unit("mm", Decimal("1e-3")),
        Unit("cm", Decimal("1e-2")),
        Unit("m", Decimal("1e0")),
        Unit("km", Decimal("1e3")),
        Unit("Mm", Decimal("1e6")),
        Unit("Gm", Decimal("1e9")),
        Unit("Tm", Decimal("1e12")),
        Unit("Pm", Decimal("1e15")),
        Unit("Em", Decimal("1e18")),
        Unit("Zm", Decimal("1e21")),
        Unit("Ym", Decimal("1e24")),
        Unit("uni", uni * Decimal("1e0")),
        Unit("kuni", uni * Decimal("1e3")),
        Unit("Muni", uni * Decimal("1e6")),
        Unit("Guni", uni * Decimal("1e9")),
        Unit("Tuni", uni * Decimal("1e12")),
        Unit("Puni", uni * Decimal("1e15")),
        Unit("Euni", uni * Decimal("1e18")),
        Unit("Zuni", uni * Decimal("1e21")),
        Unit("Yuni", uni * Decimal("1e24")),
        FixedUnit("∞", uni * Decimal("1e27"))
    ], key=lambda u: u.factor),
    "u": sorted([
        Unit("ym", Decimal("1e-24")),
        Unit("zm", Decimal("1e-21")),
        Unit("am", Decimal("1e-18")),
        Unit("fm", Decimal("1e-15")),
        Unit("pm", Decimal("1e-12")),
        Unit("nm", Decimal("1e-9")),
        Unit("µm", Decimal("1e-6")),
        Unit("mm", Decimal("1e-3")),
        Unit("in", inch),
        FeetAndInchesUnit("'", "\"", foot),
        Unit("mi", mile),
        Unit("AU", au),
        Unit("ly", ly),
        Unit("uni", uni * Decimal("1e0")),
        Unit("kuni", uni * Decimal("1e3")),
        Unit("Muni", uni * Decimal("1e6")),
        Unit("Guni", uni * Decimal("1e9")),
        Unit("Tuni", uni * Decimal("1e12")),
        Unit("Puni", uni * Decimal("1e15")),
        Unit("Euni", uni * Decimal("1e18")),
        Unit("Zuni", uni * Decimal("1e21")),
        Unit("Yuni", uni * Decimal("1e24")),
        FixedUnit("∞", uni * Decimal("1e27"))
    ], key=lambda u: u.factor)
}


# sorted list of units
wvunits = {
    "m": sorted([
        Unit("yg", Decimal("1e-24")),
        Unit("zg", Decimal("1e-21")),
        Unit("ag", Decimal("1e-18")),
        Unit("fg", Decimal("1e-15")),
        Unit("pg", Decimal("1e-12")),
        Unit("ng", Decimal("1e-9")),
        Unit("µg", Decimal("1e-6")),
        Unit("mg", Decimal("1e-3")),
        Unit("g", Decimal("1e0")),
        Unit("kg", Decimal("1e3")),
        Unit("t", Decimal("1e6")),
        Unit("kt", Decimal("1e9")),
        Unit("Mt", Decimal("1e12")),
        Unit("Gt", Decimal("1e15")),
        Unit("Tt", Decimal("1e18")),
        Unit("Pt", Decimal("1e21")),
        Unit("Et", Decimal("1e24")),
        Unit("Zt", Decimal("1e27")),
        Unit("Yt", Decimal("1e30")),
        Unit("uni", uniw * Decimal("1e0")),
        Unit("kuni", uniw * Decimal("1e3")),
        Unit("Muni", uniw * Decimal("1e6")),
        Unit("Guni", uniw * Decimal("1e9")),
        Unit("Tuni", uniw * Decimal("1e12")),
        Unit("Puni", uniw * Decimal("1e15")),
        Unit("Euni", uniw * Decimal("1e18")),
        Unit("Zuni", uniw * Decimal("1e21")),
        Unit("Yuni", uniw * Decimal("1e24")),
        FixedUnit("∞", uniw * Decimal("1e27"))
    ], key=lambda u: u.factor),
    "u": sorted([
        Unit("yg", Decimal("1e-24")),
        Unit("zg", Decimal("1e-21")),
        Unit("ag", Decimal("1e-18")),
        Unit("fg", Decimal("1e-15")),
        Unit("pg", Decimal("1e-12")),
        Unit("ng", Decimal("1e-9")),
        Unit("µg", Decimal("1e-6")),
        Unit("mg", Decimal("1e-3")),
        Unit("g", Decimal("1e0")),
        Unit("oz", ounce),
        Unit("lb", pound),
        Unit(" US tons", uston),
        Unit(" Earths", earth),
        Unit(" Suns", sun),
        Unit(" Milky Ways", milkyway),
        Unit("uni", uniw * Decimal("1e0")),
        Unit("kuni", uniw * Decimal("1e3")),
        Unit("Muni", uniw * Decimal("1e6")),
        Unit("Guni", uniw * Decimal("1e9")),
        Unit("Tuni", uniw * Decimal("1e12")),
        Unit("Puni", uniw * Decimal("1e15")),
        Unit("Euni", uniw * Decimal("1e18")),
        Unit("Zuni", uniw * Decimal("1e21")),
        Unit("Yuni", uniw * Decimal("1e24")),
        FixedUnit("∞", uniw * Decimal("1e27"))
    ], key=lambda u: u.factor)
}


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
    if system not in svunits.keys():
        raise errors.InvalidUnitSystemException(system)
    unit = getBestUnit(value, svunits[system])
    formatted = unit.format(value, accuracy)
    return formatted


# Convert "weight values" to a more readable format.
def fromWV(value, system = "m", accuracy = 2):
    if system not in wvunits.keys():
        raise errors.InvalidUnitSystemException(system)
    unit = getBestUnit(value, wvunits[system])
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


class SV(commands.Converter):
    async def convert(self, ctx, argument):
        heightsv = toSV(argument)
        if heightsv is None:
            raise commands.errors.BadArgument
        return heightsv
