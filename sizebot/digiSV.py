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


# Get letters from string
def getSVPair(s):
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
    if feetval is None and inchval in None:
        return value
    if feetval is None:
        feetval = "0"
    if inchval is None:
        inchval = "0"
    totalinches = (Decimal(feetval) * Decimal("12")) + Decimal(inchval)
    return f"{totalinches}in"


# Convert any supported height to "size value"
def toSV(s):
    s = isFeetAndInchesAndIfSoFixIt(s)
    value, unit = getSVPair(s)
    if value is None or unit is None:
        return None
    unit = unit.lower()
    if unit in ["yoctometers", "yoctometer"]:
        output = Decimal(value) / Decimal("1e24")
    elif unit in ["zeptometers", "zeptometer"]:
        output = Decimal(value) / Decimal("1e21")
    elif unit in ["attometers", "attometer", "am"]:
        output = Decimal(value) / Decimal("1e18")
    elif unit in ["femtometers", "femtometer", "fm"]:
        output = Decimal(value) / Decimal("1e15")
    elif unit in ["picometers", "picometer"]:
        output = Decimal(value) / Decimal("1e12")
    elif unit in ["nanometers", "nanometer", "nm"]:
        output = Decimal(value) / Decimal("1e9")
    elif unit in ["micrometers", "micrometer", "um"]:
        output = Decimal(value) / Decimal("1e6")
    elif unit in ["millimeters", "millimeter", "mm"]:
        output = Decimal(value) / Decimal("1e3")
    elif unit in ["centimeters", "centimeter", "cm"]:
        output = Decimal(value) / Decimal("1e2")
    elif unit in ["meters", "meter", "m"]:
        output = Decimal(value)
    elif unit in ["kilometers", "kilometer", "km"]:
        output = Decimal(value) * Decimal("1e3")
    elif unit in ["megameters", "megameter"]:
        output = Decimal(value) * Decimal("1e6")
    elif unit in ["gigameters", "gigameter", "gm"]:
        output = Decimal(value) * Decimal("1e9")
    elif unit in ["terameters", "terameter", "tm"]:
        output = Decimal(value) * Decimal("1e12")
    elif unit in ["petameters", "petameter", "pm"]:
        output = Decimal(value) * Decimal("1e15")
    elif unit in ["exameters", "exameter", "em"]:
        output = Decimal(value) * Decimal("1e18")
    elif unit in ["zettameters", "zettameter", "zm"]:
        output = Decimal(value) * Decimal("1e21")
    elif unit in ["yottameters", "yottameter", "ym"]:
        output = Decimal(value) * Decimal("1e24")
    elif unit in ["inches", "inch", "in", "\""]:
        output = Decimal(value) * inch
    elif unit in ["feet", "foot", "ft", "'"]:
        output = Decimal(value) * foot
    elif unit in ["miles", "mile", "mi"]:
        output = Decimal(value) * mile
    elif unit in ["lightyears", "lightyear", "ly"]:
        output = Decimal(value) * ly
    elif unit in ["astronomical_units", "astronomical_unit", "au"]:
        output = Decimal(value) * au
    elif unit in ["universes", "universe", "uni"]:
        output = Decimal(value) * uni
    elif unit in ["kilouniverses", "kilouniverse", "kuni"]:
        output = Decimal(value) * uni * Decimal("1e3")
    elif unit in ["megauniverses", "megauniverse", "muni"]:
        output = Decimal(value) * uni * Decimal("1e6")
    elif unit in ["gigauniverses", "gigauniverse", "guni"]:
        output = Decimal(value) * uni * Decimal("1e9")
    elif unit in ["terauniverses", "terauniverse", "tuni"]:
        output = Decimal(value) * uni * Decimal("1e12")
    elif unit in ["petauniverses", "petauniverse", "puni"]:
        output = Decimal(value) * uni * Decimal("1e15")
    elif unit in ["exauniverses", "exauniverse", "euni"]:
        output = Decimal(value) * uni * Decimal("1e18")
    elif unit in ["zettauniverses", "zettauniverse", "zuni"]:
        output = Decimal(value) * uni * Decimal("1e21")
    elif unit in ["yottauniverses", "yottauniverse", "yuni"]:
        output = Decimal(value) * uni * Decimal("1e24")
    else:
        return None
    return output


# Convert any supported weight to "weight value", or milligrams.
def toWV(s):
    value, unit = getSVPair(s)
    if value is None or unit is None:
        return None
    unit = unit.lower()
    if unit in ["yoctograms", "yoctograms", "yg"]:
        output = Decimal(value) / Decimal("1e24")
    elif unit in ["zeptograms", "zeptograms", "zg"]:
        output = Decimal(value) / Decimal("1e21")
    elif unit in ["attograms", "attogram", "ag"]:
        output = Decimal(value) / Decimal("1e18")
    elif unit in ["femtogram", "femtogram", "fg"]:
        output = Decimal(value) / Decimal("1e15")
    elif unit in ["picogram", "picogram", "pg"]:
        output = Decimal(value) / Decimal("1e12")
    elif unit in ["nanogram", "nanogram", "ng"]:
        output = Decimal(value) / Decimal("1e9")
    elif unit in ["microgram", "microgram", "ug"]:
        output = Decimal(value) / Decimal("1e6")
    elif unit in ["milligrams", "milligram", "mg"]:
        output = Decimal(value)
    elif unit in ["grams", "gram", "g"]:
        output = Decimal(value) * Decimal("1e3")
    elif unit in ["kilograms", "kilogram", "kg"]:
        output = Decimal(value) * Decimal("1e6")
    elif unit in ["megagrams", "megagram", "t", "ton", "tons", "tonnes", "tons"]:
        output = Decimal(value) * Decimal("1e9")
    elif unit in ["gigagrams", "gigagram", "gg", "kilotons", "kiloton", "kilotonnes", "kilotonne", "kt"]:
        output = Decimal(value) * Decimal("1e12")
    elif unit in ["teragrams", "teragram", "tg", "megatons", "megaton", "megatonnes", "megatonne", "mt"]:
        output = Decimal(value) * Decimal("1e15")
    elif unit in ["petagrams", "petagram", "gigatons", "gigaton", "gigatonnes", "gigatonnes", "gt"]:
        output = Decimal(value) * Decimal("1e18")
    elif unit in ["exagrams", "exagram", "eg", "teratons", "teraton", "teratonnes", "teratonne", "tt"]:
        output = Decimal(value) * Decimal("1e21")
    elif unit in ["zettagrams", "zettagram", "petatons", "petaton", "petatonnes", "petatonne", "pt"]:
        output = Decimal(value) * Decimal("1e24")
    elif unit in ["yottagrams", "yottagram", "exatons", "exaton", "exatonnes", "exatonne", "et"]:
        output = Decimal(value) * Decimal("1e27")
    elif unit in ["zettatons", "zettaton", "zettatonnes", "zettatonne", "zt"]:
        output = Decimal(value) * Decimal("1e30")
    elif unit in ["yottatons", "yottaton", "yottatonnes", "yottatonne", "yt"]:
        output = Decimal(value) * Decimal("1e33")
    elif unit in ["universes", "universe", "uni"]:
        output = Decimal(value) * uniw
    elif unit in ["kilouniverses", "kilouniverse", "kuni"]:
        output = Decimal(value) * uniw * Decimal("1e3")
    elif unit in ["megauniverses", "megauniverse", "muni"]:
        output = Decimal(value) * uniw * Decimal("1e6")
    elif unit in ["gigauniverses", "gigauniverse", "guni"]:
        output = Decimal(value) * uniw * Decimal("1e9")
    elif unit in ["terauniverses", "terauniverse", "tuni"]:
        output = Decimal(value) * uniw * Decimal("1e12")
    elif unit in ["petauniverses", "petauniverse", "puni"]:
        output = Decimal(value) * uniw * Decimal("1e15")
    elif unit in ["exauniverses", "exauniverse", "euni"]:
        output = Decimal(value) * uniw * Decimal("1e18")
    elif unit in ["zettauniverses", "zettauniverse", "zuni"]:
        output = Decimal(value) * uniw * Decimal("1e21")
    elif unit in ["yottauniverses", "yottauniverse", "yuni"]:
        output = Decimal(value) * uniw * Decimal("1e24")
    elif unit in ["ounces", "ounce", "oz"]:
        output = Decimal(value) * ounce
    elif unit in ["pounds", "pound", "lb", "lbs"]:
        output = Decimal(value) * pound
    elif unit in ["earth", "earths"]:
        output = Decimal(value) * earth
    elif unit in ["sun", "suns"]:
        output = Decimal(value) * sun
    else:
        return None
    return output


# Unit: Formats a value by scaling it and applying the appropriate symbol suffix
class Unit():
    def __init__(self, symbol, factor):
        self.symbol = symbol
        self.factor = factor

    def format(self, value, accuracy):
        scaled = value / self.factor
        rounded = roundDecimal(scaled, accuracy)
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
    if value <= 0:
        return "0"
    if system not in svunits.keys():
        raise errors.InvalidUnitSystemException(system)
    unit = getBestUnit(value, svunits[system])
    formatted = unit.format(value)
    return formatted


# Convert "weight values" to a more readable format.
def fromWV(value, system = "m", accuracy = 2):
    if value <= 0:
        return "0"
    if system not in wvunits.keys():
        raise errors.InvalidUnitSystemException(system)
    unit = getBestUnit(value, wvunits[system])
    formatted = unit.format(value)
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
