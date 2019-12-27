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


# Convert "size values" to a more readable format (metric).
def fromSV(value, system = "m", accuracy = 2):
    PLACES = Decimal(10) ** -accuracy
    value = float(value)
    output = ""
    if system == "m":
        if value <= Decimal("0"):
            return "0"
        elif value < Decimal("0.000000000000000000001"):
            output = str((Decimal(value) * Decimal("1e18")).quantize(PLACES)) + "ym"
        elif value < Decimal("0.000000000000000001"):
            output = str((Decimal(value) * Decimal("1e15")).quantize(PLACES)) + "zm"
        elif value < Decimal("0.000000000000001"):
            output = str((Decimal(value) * Decimal("1e12")).quantize(PLACES)) + "am"
        elif value < Decimal("0.000000000001"):
            output = str((Decimal(value) * Decimal("1e9")).quantize(PLACES)) + "fm"
        elif value < Decimal("0.000000001"):
            output = str((Decimal(value) * Decimal("1e6")).quantize(PLACES)) + "pm"
        elif value < Decimal("0.0000001"):
            output = str((Decimal(value) * Decimal("1e3")).quantize(PLACES)) + "nm"
        elif value < Decimal("0.00001"):
            output = str((Decimal(value)).quantize(PLACES)) + "µm"
        elif value < Decimal("0.01"):
            output = str((Decimal(value) / Decimal("1e3")).quantize(PLACES)) + "mm"
        elif value < Decimal("10"):
            output = str((Decimal(value) / Decimal("1e4")).quantize(PLACES)) + "cm"
        elif value < Decimal("1e3"):
            output = str((Decimal(value) / Decimal("1e6")).quantize(PLACES)) + "m"
        elif value < Decimal("1e6"):
            output = str((Decimal(value) / Decimal("1e9")).quantize(PLACES)) + "km"
        elif value < Decimal("1e9"):
            output = str((Decimal(value) / Decimal("1e12")).quantize(PLACES)) + "Mm"
        elif value < Decimal("1e12"):
            output = str((Decimal(value) / Decimal("1e15")).quantize(PLACES)) + "Gm"
        elif value < Decimal("1e15"):
            output = str((Decimal(value) / Decimal("1e18")).quantize(PLACES)) + "Tm"
        elif value < Decimal("1e18"):
            output = str((Decimal(value) / Decimal("1e21")).quantize(PLACES)) + "Pm"
        elif value < Decimal("1e21"):
            output = str((Decimal(value) / Decimal("1e24")).quantize(PLACES)) + "Em"
        elif value < Decimal("1e24"):
            output = str((Decimal(value) / Decimal("1e27")).quantize(PLACES)) + "Zm"
        elif value < uni:
            output = str((Decimal(value) / Decimal("1e30")).quantize(PLACES)) + "Ym"
        elif value < uni * Decimal("1e3"):
            output = str((Decimal(value) / uni).quantize(PLACES)) + "uni"
        elif value < uni * Decimal("1e6"):
            output = str((Decimal(value) / uni / Decimal("1e3")).quantize(PLACES)) + "kuni"
        elif value < uni * Decimal("1e9"):
            output = str((Decimal(value) / uni / Decimal("1e6")).quantize(PLACES)) + "Muni"
        elif value < uni * Decimal("1e12"):
            output = str((Decimal(value) / uni / Decimal("1e9")).quantize(PLACES)) + "Guni"
        elif value < uni * Decimal("1e15"):
            output = str((Decimal(value) / uni / Decimal("1e12")).quantize(PLACES)) + "Tuni"
        elif value < uni * Decimal("1e18"):
            output = str((Decimal(value) / uni / Decimal("1e15")).quantize(PLACES)) + "Puni"
        elif value < uni * Decimal("1e21"):
            output = str((Decimal(value) / uni / Decimal("1e18")).quantize(PLACES)) + "Euni"
        elif value < uni * Decimal("1e24"):
            output = str((Decimal(value) / uni / Decimal("1e21")).quantize(PLACES)) + "Zuni"
        elif value < uni * Decimal("1e27"):
            output = str((Decimal(value) / uni / Decimal("1e24")).quantize(PLACES)) + "Yuni"
        else:
            return "∞"
    elif system == "u":
        if value <= Decimal("0"):
            return "0"
        elif value < Decimal("0.000000000000000000001"):
            output = str((Decimal(value) * Decimal("1e18")).quantize(PLACES)) + "ym"
        elif value < Decimal("0.000000000000000001"):
            output = str((Decimal(value) * Decimal("1e15")).quantize(PLACES)) + "zm"
        elif value < Decimal("0.000000000000001"):
            output = str((Decimal(value) * Decimal("1e12")).quantize(PLACES)) + "am"
        elif value < Decimal("0.000000000001"):
            output = str((Decimal(value) * Decimal("1e9")).quantize(PLACES)) + "fm"
        elif value < Decimal("0.000000001"):
            output = str((Decimal(value) * Decimal("1e6")).quantize(PLACES)) + "pm"
        elif value < Decimal("0.000001"):
            output = str((Decimal(value) * Decimal("1e3")).quantize(PLACES)) + "nm"
        elif value < Decimal("0.0001"):
            output = str((Decimal(value)).quantize(PLACES)) + "µm"
        elif value < Decimal("0.01"):
            output = str((Decimal(value) / Decimal("1e3")).quantize(PLACES)) + "mm"
        elif value < foot:
            output = str((Decimal(value) / inch).quantize(PLACES)) + "in"
        elif value < mile:
            feetval = math.floor(Decimal(value) / foot)
            fulloninches = (Decimal(value) / inch).quantize(PLACES)
            feettoinches = feetval * Decimal(12)
            inchval = fulloninches - feettoinches
            output = str(feetval) + "'" + str(inchval) + "\""
        elif value < au:
            output = str((Decimal(value) / mile).quantize(PLACES)) + "mi"
        elif value < ly:
            output = str((Decimal(value) / au).quantize(PLACES)) + "AU"
        elif value < uni / Decimal("10"):
            output = str((Decimal(value) / ly).quantize(PLACES)) + "ly"
        elif value < uni * Decimal("1e3"):
            output = str((Decimal(value) / uni).quantize(PLACES)) + "uni"
        elif value < uni * Decimal("1e6"):
            output = str((Decimal(value) / uni / Decimal(1e3)).quantize(PLACES)) + "kuni"
        elif value < uni * Decimal("1e9"):
            output = str((Decimal(value) / uni / Decimal(1e6)).quantize(PLACES)) + "Muni"
        elif value < uni * Decimal("1e12"):
            output = str((Decimal(value) / uni / Decimal(1e9)).quantize(PLACES)) + "Guni"
        elif value < uni * Decimal("1e15"):
            output = str((Decimal(value) / uni / Decimal(1e12)).quantize(PLACES)) + "Tuni"
        elif value < uni * Decimal("1e18"):
            output = str((Decimal(value) / uni / Decimal(1e15)).quantize(PLACES)) + "Puni"
        elif value < uni * Decimal("1e21"):
            output = str((Decimal(value) / uni / Decimal(1e18)).quantize(PLACES)) + "Euni"
        elif value < uni * Decimal("1e24"):
            output = str((Decimal(value) / uni / Decimal(1e21)).quantize(PLACES)) + "Zuni"
        elif value < uni * Decimal("1e27"):
            output = str((Decimal(value) / uni / Decimal(1e24)).quantize(PLACES)) + "Yuni"
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
def fromWV(value, system = "m", accuracy = 2):
    PLACES = Decimal(10) ** -accuracy
    value = Decimal(value)
    if system == "m":
        if value <= Decimal("0"):
            return "0"
        elif value < Decimal("0.000000000000000000001"):
            output = str((Decimal(value) * Decimal(1e21)).quantize(PLACES)) + "yg"
        elif value < Decimal("0.000000000000000001"):
            output = str((Decimal(value) * Decimal(1e18)).quantize(PLACES)) + "zg"
        elif value < Decimal("0.000000000000001"):
            output = str((Decimal(value) * Decimal(1e15)).quantize(PLACES)) + "ag"
        elif value < Decimal("0.000000000001"):
            output = str((Decimal(value) * Decimal(1e12)).quantize(PLACES)) + "fg"
        elif value < Decimal("0.000000001"):
            output = str((Decimal(value) * Decimal(1e9)).quantize(PLACES)) + "pg"
        elif value < Decimal("0.000001"):
            output = str((Decimal(value) * Decimal(1e6)).quantize(PLACES)) + "ng"
        elif value < Decimal("0.001"):
            output = str((Decimal(value) * Decimal(1e3)).quantize(PLACES)) + "µg"
        elif value < Decimal("1"):
            output = str((Decimal(value)).quantize(PLACES)) + "mg"
        elif value < Decimal("10000"):
            output = str((Decimal(value) / Decimal(1e3)).quantize(PLACES)) + "g"
        elif value < Decimal("1000000"):
            output = str((Decimal(value) / Decimal(1e6)).quantize(PLACES)) + "kg"
        elif value < Decimal("100000000"):
            output = str((Decimal(value) / Decimal(1e9)).quantize(PLACES)) + "t"
        elif value < Decimal("100000000000"):
            output = str((Decimal(value) / Decimal(1e12)).quantize(PLACES)) + "kt"
        elif value < Decimal("100000000000000"):
            output = str((Decimal(value) / Decimal(1e15)).quantize(PLACES)) + "Mt"
        elif value < Decimal("100000000000000000"):
            output = str((Decimal(value) / Decimal(1e18)).quantize(PLACES)) + "Gt"
        elif value < Decimal("100000000000000000000"):
            output = str((Decimal(value) / Decimal(1e21)).quantize(PLACES)) + "Tt"
        elif value < Decimal("100000000000000000000000"):
            output = str((Decimal(value) / Decimal(1e24)).quantize(PLACES)) + "Pt"
        elif value < Decimal("100000000000000000000000000"):
            output = str((Decimal(value) / Decimal(1e27)).quantize(PLACES)) + "Et"
        elif value < Decimal("100000000000000000000000000000"):
            output = str((Decimal(value) / Decimal(1e30)).quantize(PLACES)) + "Zt"
        elif value < Decimal("100000000000000000000000000000000"):
            output = str((Decimal(value) / Decimal(1e33)).quantize(PLACES)) + "Yt"
        elif value < uniw * Decimal("1e3"):
            output = str((Decimal(value) / uniw).quantize(PLACES)) + "uni"
        elif value < uniw * Decimal("1e6"):
            output = str((Decimal(value) / uniw / Decimal("1e3")).quantize(PLACES)) + "kuni"
        elif value < uniw * Decimal("1e9"):
            output = str((Decimal(value) / uniw / Decimal("1e6")).quantize(PLACES)) + "Muni"
        elif value < uniw * Decimal("1e12"):
            output = str((Decimal(value) / uniw / Decimal("1e9")).quantize(PLACES)) + "Guni"
        elif value < uniw * Decimal("1e15"):
            output = str((Decimal(value) / uniw / Decimal("1e12")).quantize(PLACES)) + "Tuni"
        elif value < uniw * Decimal("1e18"):
            output = str((Decimal(value) / uniw / Decimal("1e15")).quantize(PLACES)) + "Puni"
        elif value < uniw * Decimal("1e21"):
            output = str((Decimal(value) / uniw / Decimal("1e18")).quantize(PLACES)) + "Euni"
        elif value < uniw * Decimal("1e24"):
            output = str((Decimal(value) / uniw / Decimal("1e21")).quantize(PLACES)) + "Zuni"
        elif value < uniw * Decimal("1e27"):
            output = str((Decimal(value) / uniw / Decimal("1e24")).quantize(PLACES)) + "Yuni"
        else:
            return "∞"
    elif system == "u":
        if value == 0:
            return "almost nothing"
        elif value < Decimal("0.000000000000000000001"):
            output = str((Decimal(value) * Decimal("1e21")).quantize(PLACES)) + "yg"
        elif value < Decimal("0.000000000000000001"):
            output = str((Decimal(value) * Decimal("1e18")).quantize(PLACES)) + "zg"
        elif value < Decimal("0.000000000000001"):
            output = str((Decimal(value) * Decimal("1e15")).quantize(PLACES)) + "ag"
        elif value < Decimal("0.000000000001"):
            output = str((Decimal(value) * Decimal("1e12")).quantize(PLACES)) + "fg"
        elif value < Decimal("0.000000001"):
            output = str((Decimal(value) * Decimal("1e9")).quantize(PLACES)) + "pg"
        elif value < Decimal("0.000001"):
            output = str((Decimal(value) * Decimal("1e6")).quantize(PLACES)) + "ng"
        elif value < Decimal("0.001"):
            output = str((Decimal(value) * Decimal("1e3")).quantize(PLACES)) + "µg"
        elif value < Decimal("1"):
            output = str((Decimal(value)).quantize(PLACES)) + "mg"
        elif value < ounce / Decimal("10"):
            output = str((Decimal(value) / Decimal("1e3")).quantize(PLACES)) + "g"
        elif value < pound:
            output = str(placeValue((Decimal(value) / ounce).quantize(PLACES))) + "oz"
        elif value < uston:
            output = str(placeValue((Decimal(value) / pound).quantize(PLACES))) + "lb"
        elif value < earth / Decimal("10"):
            output = str(placeValue((Decimal(value) / uston).quantize(PLACES))) + " US tons"
        elif value < sun / Decimal("10"):
            output = str(placeValue((Decimal(value) / earth).quantize(PLACES))) + " Earths"
        elif value < milkyway:
            output = str(placeValue((Decimal(value) / sun).quantize(PLACES))) + " Suns"
        elif value < uniw:
            output = str(placeValue((Decimal(value) / milkyway).quantize(PLACES))) + " Milky Ways"
        elif value < uniw * Decimal("1e3"):
            output = str((Decimal(value) / uniw).quantize(PLACES)) + "uni"
        elif value < uniw * Decimal("1e6"):
            output = str((Decimal(value) / uniw / Decimal("1e3")).quantize(PLACES)) + "kuni"
        elif value < uniw * Decimal("1e9"):
            output = str((Decimal(value) / uniw / Decimal("1e6")).quantize(PLACES)) + "Muni"
        elif value < uniw * Decimal("1e12"):
            output = str((Decimal(value) / uniw / Decimal("1e9")).quantize(PLACES)) + "Guni"
        elif value < uniw * Decimal("1e15"):
            output = str((Decimal(value) / uniw / Decimal("1e12")).quantize(PLACES)) + "Tuni"
        elif value < uniw * Decimal("1e18"):
            output = str((Decimal(value) / uniw / Decimal("1e15")).quantize(PLACES)) + "Puni"
        elif value < uniw * Decimal("1e21"):
            output = str((Decimal(value) / uniw / Decimal("1e18")).quantize(PLACES)) + "Euni"
        elif value < uniw * Decimal("1e24"):
            output = str((Decimal(value) / uniw / Decimal("1e21")).quantize(PLACES)) + "Zuni"
        elif value < uniw * Decimal("1e27"):
            output = str((Decimal(value) / uniw / Decimal("1e24")).quantize(PLACES)) + "Yuni"
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
