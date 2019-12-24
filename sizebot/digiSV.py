import math
import re

from sizebot.digidecimal import Decimal

# Unit constants.
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


def roundNearestHalf(number):
    return round(number * Decimal("2")) / Decimal("2")


def placeValue(number):
    return "{:,}".format(number)


# Remove decimals
def removeDecimals(output):
    if re.search(r"(\.\d*?)(0+)", output):
        output = re.sub(r"(\.\d*?)(0+)", r"\1", output)
    if re.search(r"(.*)(\.)(\D+)", output):
        output = re.sub(r"(.*)(\.)(\D+)", r"\1\3", output)
    return output


# Get number from string
def getNum(s):
    match = re.search(r"", s)
    if match is None:
        return None
    return Decimal(match.group(0))


# Get letters from string
def getSVPair(s):
    match = re.search(r"(\d+\.?\d*) *([a-zA-Z\'\"]+)", s)
    value, unit = None, None
    if match is not None:
        value, unit = match.group(1), match.group(2)
    return value, unit


def isFeetAndInchesAndIfSoFixIt(value):
    regex = r"^(?P<feet>\d+\.?\d*(ft|foot|feet|'))?(?P<inch>\d+\.?\d*(in|\"))?"
    m = re.match(regex, value, flags = re.I)
    if not m:
        return value
    feetval = m.group("feet")
    inchval = m.group("inch")
    if feetval is None and inchval in None:
        return value
    if feetval is None:
        feetval = Decimal("0")
    if inchval is None:
        inchval = Decimal("0")
    totalinches = (feetval * Decimal("12")) + inchval
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


# Convert "size values" to a more readable format (metric).
def fromSV(value, system = "m", accuracy = Decimal("2")):
    value = float(value)
    output = ""
    if system == "m":
        if value <= Decimal("0"):
            return "0"
        elif value < Decimal("0.000000000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e18"), accuracy)) + "ym"
        elif value < Decimal("0.000000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e15"), accuracy)) + "zm"
        elif value < Decimal("0.000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e12"), accuracy)) + "am"
        elif value < Decimal("0.000000000001"):
            output = str(round(Decimal(value) * Decimal("1e9"), accuracy)) + "fm"
        elif value < Decimal("0.000000001"):
            output = str(round(Decimal(value) * Decimal("1e6"), accuracy)) + "pm"
        elif value < Decimal("0.0000001"):
            output = str(round(Decimal(value) * Decimal("1e3"), accuracy)) + "nm"
        elif value < Decimal("0.00001"):
            output = str(round(Decimal(value), accuracy)) + "µm"
        elif value < Decimal("0.01"):
            output = str(round(Decimal(value) / Decimal("1e3"), accuracy)) + "mm"
        elif value < Decimal("10"):
            output = str(round(Decimal(value) / Decimal("1e4"), accuracy)) + "cm"
        elif value < Decimal("1e3"):
            output = str(round(Decimal(value) / Decimal("1e6"), accuracy)) + "m"
        elif value < Decimal("1e6"):
            output = str(round(Decimal(value) / Decimal("1e9"), accuracy)) + "km"
        elif value < Decimal("1e9"):
            output = str(round(Decimal(value) / Decimal("1e12"), accuracy)) + "Mm"
        elif value < Decimal("1e12"):
            output = str(round(Decimal(value) / Decimal("1e15"), accuracy)) + "Gm"
        elif value < Decimal("1e15"):
            output = str(round(Decimal(value) / Decimal("1e18"), accuracy)) + "Tm"
        elif value < Decimal("1e18"):
            output = str(round(Decimal(value) / Decimal("1e21"), accuracy)) + "Pm"
        elif value < Decimal("1e21"):
            output = str(round(Decimal(value) / Decimal("1e24"), accuracy)) + "Em"
        elif value < Decimal("1e24"):
            output = str(round(Decimal(value) / Decimal("1e27"), accuracy)) + "Zm"
        elif value < uni:
            output = str(round(Decimal(value) / Decimal("1e30"), accuracy)) + "Ym"
        elif value < uni * Decimal("1e3"):
            output = str(round(Decimal(value) / uni, accuracy)) + "uni"
        elif value < uni * Decimal("1e6"):
            output = str(round(Decimal(value) / uni / Decimal("1e3"), accuracy)) + "kuni"
        elif value < uni * Decimal("1e9"):
            output = str(round(Decimal(value) / uni / Decimal("1e6"), accuracy)) + "Muni"
        elif value < uni * Decimal("1e12"):
            output = str(round(Decimal(value) / uni / Decimal("1e9"), accuracy)) + "Guni"
        elif value < uni * Decimal("1e15"):
            output = str(round(Decimal(value) / uni / Decimal("1e12"), accuracy)) + "Tuni"
        elif value < uni * Decimal("1e18"):
            output = str(round(Decimal(value) / uni / Decimal("1e15"), accuracy)) + "Puni"
        elif value < uni * Decimal("1e21"):
            output = str(round(Decimal(value) / uni / Decimal("1e18"), accuracy)) + "Euni"
        elif value < uni * Decimal("1e24"):
            output = str(round(Decimal(value) / uni / Decimal("1e21"), accuracy)) + "Zuni"
        elif value < uni * Decimal("1e27"):
            output = str(round(Decimal(value) / uni / Decimal("1e24"), accuracy)) + "Yuni"
        else:
            return "∞"
    elif system == "u":
        if value <= Decimal("0"):
            return "0"
        elif value < Decimal("0.000000000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e18"), accuracy)) + "ym"
        elif value < Decimal("0.000000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e15"), accuracy)) + "zm"
        elif value < Decimal("0.000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e12"), accuracy)) + "am"
        elif value < Decimal("0.000000000001"):
            output = str(round(Decimal(value) * Decimal("1e9"), accuracy)) + "fm"
        elif value < Decimal("0.000000001"):
            output = str(round(Decimal(value) * Decimal("1e6"), accuracy)) + "pm"
        elif value < Decimal("0.000001"):
            output = str(round(Decimal(value) * Decimal("1e3"), accuracy)) + "nm"
        elif value < Decimal("0.0001"):
            output = str(round(Decimal(value), accuracy)) + "µm"
        elif value < Decimal("0.01"):
            output = str(round(Decimal(value) / Decimal("1e3"), accuracy)) + "mm"
        elif value < foot:
            output = str(round(Decimal(value) / inch, accuracy)) + "in"
        elif value < mile:
            feetval = math.floor(Decimal(value) / foot)
            fulloninches = round(Decimal(value) / inch, accuracy)
            feettoinches = feetval * Decimal(12)
            inchval = fulloninches - feettoinches
            output = str(feetval) + "'" + str(inchval) + "\""
        elif value < au:
            output = str(round(Decimal(value) / mile, accuracy)) + "mi"
        elif value < ly:
            output = str(round(Decimal(value) / au, accuracy)) + "AU"
        elif value < uni / Decimal("10"):
            output = str(round(Decimal(value) / ly, accuracy)) + "ly"
        elif value < uni * Decimal("1e3"):
            output = str(round(Decimal(value) / uni, accuracy)) + "uni"
        elif value < uni * Decimal("1e6"):
            output = str(round(Decimal(value) / uni / Decimal(1e3), accuracy)) + "kuni"
        elif value < uni * Decimal("1e9"):
            output = str(round(Decimal(value) / uni / Decimal(1e6), accuracy)) + "Muni"
        elif value < uni * Decimal("1e12"):
            output = str(round(Decimal(value) / uni / Decimal(1e9), accuracy)) + "Guni"
        elif value < uni * Decimal("1e15"):
            output = str(round(Decimal(value) / uni / Decimal(1e12), accuracy)) + "Tuni"
        elif value < uni * Decimal("1e18"):
            output = str(round(Decimal(value) / uni / Decimal(1e15), accuracy)) + "Puni"
        elif value < uni * Decimal("1e21"):
            output = str(round(Decimal(value) / uni / Decimal(1e18), accuracy)) + "Euni"
        elif value < uni * Decimal("1e24"):
            output = str(round(Decimal(value) / uni / Decimal(1e21), accuracy)) + "Zuni"
        elif value < uni * Decimal("1e27"):
            output = str(round(Decimal(value) / uni / Decimal(1e24), accuracy)) + "Yuni"
        else:
            return "∞"
    return removeDecimals(output)


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


# Convert "weight values" to a more readable format.
def fromWV(value, system = "m", accuracy = Decimal("2")):
    value = Decimal(value)
    if system == "m":
        if value <= Decimal("0"):
            return "0"
        elif value < Decimal("0.000000000000000000001"):
            output = str(round(Decimal(value) * Decimal(1e21), accuracy)) + "yg"
        elif value < Decimal("0.000000000000000001"):
            output = str(round(Decimal(value) * Decimal(1e18), accuracy)) + "zg"
        elif value < Decimal("0.000000000000001"):
            output = str(round(Decimal(value) * Decimal(1e15), accuracy)) + "ag"
        elif value < Decimal("0.000000000001"):
            output = str(round(Decimal(value) * Decimal(1e12), accuracy)) + "fg"
        elif value < Decimal("0.000000001"):
            output = str(round(Decimal(value) * Decimal(1e9), accuracy)) + "pg"
        elif value < Decimal("0.000001"):
            output = str(round(Decimal(value) * Decimal(1e6), accuracy)) + "ng"
        elif value < Decimal("0.001"):
            output = str(round(Decimal(value) * Decimal(1e3), accuracy)) + "µg"
        elif value < Decimal("1"):
            output = str(round(Decimal(value), accuracy)) + "mg"
        elif value < Decimal("10000"):
            output = str(round(Decimal(value) / Decimal(1e3), accuracy)) + "g"
        elif value < Decimal("1000000"):
            output = str(round(Decimal(value) / Decimal(1e6), accuracy)) + "kg"
        elif value < Decimal("100000000"):
            output = str(round(Decimal(value) / Decimal(1e9), accuracy)) + "t"
        elif value < Decimal("100000000000"):
            output = str(round(Decimal(value) / Decimal(1e12), accuracy)) + "kt"
        elif value < Decimal("100000000000000"):
            output = str(round(Decimal(value) / Decimal(1e15), accuracy)) + "Mt"
        elif value < Decimal("100000000000000000"):
            output = str(round(Decimal(value) / Decimal(1e18), accuracy)) + "Gt"
        elif value < Decimal("100000000000000000000"):
            output = str(round(Decimal(value) / Decimal(1e21), accuracy)) + "Tt"
        elif value < Decimal("100000000000000000000000"):
            output = str(round(Decimal(value) / Decimal(1e24), accuracy)) + "Pt"
        elif value < Decimal("100000000000000000000000000"):
            output = str(round(Decimal(value) / Decimal(1e27), accuracy)) + "Et"
        elif value < Decimal("100000000000000000000000000000"):
            output = str(round(Decimal(value) / Decimal(1e30), accuracy)) + "Zt"
        elif value < Decimal("100000000000000000000000000000000"):
            output = str(round(Decimal(value) / Decimal(1e33), accuracy)) + "Yt"
        elif value < uniw * Decimal("1e3"):
            output = str(round(Decimal(value) / uniw, accuracy)) + "uni"
        elif value < uniw * Decimal("1e6"):
            output = str(round(Decimal(value) / uniw / Decimal("1e3"), accuracy)) + "kuni"
        elif value < uniw * Decimal("1e9"):
            output = str(round(Decimal(value) / uniw / Decimal("1e6"), accuracy)) + "Muni"
        elif value < uniw * Decimal("1e12"):
            output = str(round(Decimal(value) / uniw / Decimal("1e9"), accuracy)) + "Guni"
        elif value < uniw * Decimal("1e15"):
            output = str(round(Decimal(value) / uniw / Decimal("1e12"), accuracy)) + "Tuni"
        elif value < uniw * Decimal("1e18"):
            output = str(round(Decimal(value) / uniw / Decimal("1e15"), accuracy)) + "Puni"
        elif value < uniw * Decimal("1e21"):
            output = str(round(Decimal(value) / uniw / Decimal("1e18"), accuracy)) + "Euni"
        elif value < uniw * Decimal("1e24"):
            output = str(round(Decimal(value) / uniw / Decimal("1e21"), accuracy)) + "Zuni"
        elif value < uniw * Decimal("1e27"):
            output = str(round(Decimal(value) / uniw / Decimal("1e24"), accuracy)) + "Yuni"
        else:
            return "∞"
    elif system == "u":
        if value == 0:
            return "almost nothing"
        elif value < Decimal("0.000000000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e21"), accuracy)) + "yg"
        elif value < Decimal("0.000000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e18"), accuracy)) + "zg"
        elif value < Decimal("0.000000000000001"):
            output = str(round(Decimal(value) * Decimal("1e15"), accuracy)) + "ag"
        elif value < Decimal("0.000000000001"):
            output = str(round(Decimal(value) * Decimal("1e12"), accuracy)) + "fg"
        elif value < Decimal("0.000000001"):
            output = str(round(Decimal(value) * Decimal("1e9"), accuracy)) + "pg"
        elif value < Decimal("0.000001"):
            output = str(round(Decimal(value) * Decimal("1e6"), accuracy)) + "ng"
        elif value < Decimal("0.001"):
            output = str(round(Decimal(value) * Decimal("1e3"), accuracy)) + "µg"
        elif value < Decimal("1"):
            output = str(round(Decimal(value), accuracy)) + "mg"
        elif value < ounce / Decimal("10"):
            output = str(round(Decimal(value) / Decimal("1e3"), accuracy)) + "g"
        elif value < pound:
            output = str(placeValue(round(Decimal(value) / ounce, accuracy))) + "oz"
        elif value < uston:
            output = str(placeValue(round(Decimal(value) / pound, accuracy))) + "lb"
        elif value < earth / Decimal("10"):
            output = str(placeValue(round(Decimal(value) / uston, accuracy))) + " US tons"
        elif value < sun / Decimal("10"):
            output = str(placeValue(round(Decimal(value) / earth, accuracy))) + " Earths"
        elif value < milkyway:
            output = str(placeValue(round(Decimal(value) / sun, accuracy))) + " Suns"
        elif value < uniw:
            output = str(placeValue(round(Decimal(value) / milkyway, accuracy))) + " Milky Ways"
        elif value < uniw * Decimal("1e3"):
            output = str(round(Decimal(value) / uniw, accuracy)) + "uni"
        elif value < uniw * Decimal("1e6"):
            output = str(round(Decimal(value) / uniw / Decimal("1e3"), accuracy)) + "kuni"
        elif value < uniw * Decimal("1e9"):
            output = str(round(Decimal(value) / uniw / Decimal("1e6"), accuracy)) + "Muni"
        elif value < uniw * Decimal("1e12"):
            output = str(round(Decimal(value) / uniw / Decimal("1e9"), accuracy)) + "Guni"
        elif value < uniw * Decimal("1e15"):
            output = str(round(Decimal(value) / uniw / Decimal("1e12"), accuracy)) + "Tuni"
        elif value < uniw * Decimal("1e18"):
            output = str(round(Decimal(value) / uniw / Decimal("1e15"), accuracy)) + "Puni"
        elif value < uniw * Decimal("1e21"):
            output = str(round(Decimal(value) / uniw / Decimal("1e18"), accuracy)) + "Euni"
        elif value < uniw * Decimal("1e24"):
            output = str(round(Decimal(value) / uniw / Decimal("1e21"), accuracy)) + "Zuni"
        elif value < uniw * Decimal("1e27"):
            output = str(round(Decimal(value) / uniw / Decimal("1e24"), accuracy)) + "Yuni"
        else:
            return "∞"
    return removeDecimals(output)


def toShoeSize(inchamount):
    child = False
    inches = Decimal(inchamount)
    shoesize = Decimal("3") * inches
    shoesize = shoesize - Decimal("22")
    if shoesize < Decimal("1"):
        child = True
        shoesize += Decimal("12") + Decimal("1") / Decimal("3")
    if shoesize < Decimal("1"):
        return "No shoes exist this small!"
    shoesize = placeValue(roundNearestHalf(shoesize))
    if child:
        shoesize = "Children's " + shoesize
    return "Size US " + shoesize


# Currently unused.
def fromShoeSize(size):
    child = False
    if "c" in size.toLower():
        child = True
    size = getNum(size)
    inches = Decimal(size) + Decimal("22")
    if child:
        inches = Decimal(size) + Decimal("22") - Decimal("12") - (Decimal("1") / Decimal("3"))
    inches = inches / Decimal("3")
    out = inches * inch
    return out
