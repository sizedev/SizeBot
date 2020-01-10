import re
import collections

from sizebot.digidecimal import Decimal, roundDecimal, trimZeroes, toFraction
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

    def __init__(self, factor=Decimal("1"), symbol=None, name=None, namePlural=None, symbols=[], names=[], fractional=False):
        self.fractional = fractional
        self.factor = factor

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

    def format(self, value, accuracy=2, spec="", preferName=False, useFractional=False):
        scaled = value / self.factor
        useFractional = useFractional and self.fractional
        if useFractional:
            rounded = trimZeroes(scaled)
            formattedValue = toFraction(rounded, 8, spec)
        else:
            rounded = trimZeroes(roundDecimal(scaled, accuracy))
            formattedValue = format(rounded, spec)

        if rounded == 0:
            return "0"

        single = abs(rounded) == 1
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

    def toUnitValue(self, v):
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

    def toUnitValue(self, v):
        return self.factor


class FeetAndInchesUnit(Unit):
    """Unit for handling feet and inches"""
    hidden = True

    def __init__(self, footsymbol, inchsymbol, factor):
        self.footsymbol = footsymbol
        self.inchsymbol = inchsymbol
        self.factor = factor

    def format(self, value, accuracy=2, spec="", preferName=False, useFractional=False):
        inchval = value / SV.inch                  # convert to inches
        feetval, inchval = divmod(inchval, 12)  # divide by 12 to get feet, and the remainder inches
        if useFractional:
            roundedinchval = trimZeroes(roundDecimal(inchval, accuracy))
            formattedInch = toFraction(roundedinchval, 8, spec)
        else:
            rounded = trimZeroes(scaled)
            formattedInch = format(rounded, spec)
        formatted = f"{trimZeroes(feetval)}{self.footsymbol}{formattedInch}{self.inchsymbol}"
        return formatted

    def isUnit(self, u):
        return u == (self.footsymbol, self.inchsymbol)

    def toUnitValue(self, v):
        return None


class UnitRegistry(collections.abc.Mapping):
    """Unit Registry"""

    def __init__(self, units):
        self._units = units

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


class SystemRegistry():
    """System Registry"""

    def __init__(self, units, systemunits):
        for sunit in systemunits:
            sunit.load(units)
        self._systemunits = sorted(systemunits)

    # Try to find the best fitting unit, picking the largest unit if all units are too small
    def getBestUnit(self, value):
        value = abs(value)
        # Pair each unit with the unit following it
        for sunit, nextsunit in zip(self._systemunits[:-1], self._systemunits[1:]):
            # If we're smaller than the next unit's lowest value, then just use this unit
            if value < nextsunit.trigger:
                return sunit.unit
        # If we're too big for all the units, just use the biggest possible unit
        return self._systemunits[-1].unit


class SystemUnit():
    """System Units"""

    def __init__(self, unitname, trigger=None):
        self.unitname = unitname
        self._trigger = trigger
        self.unit = None

    def load(self, units):
        self.unit = units[self.unitname]

    @property
    def trigger(self):
        if self._trigger is not None:
            return self._trigger
        return self.unit.factor

    def __lt__(self, other):
        return self.trigger < other.trigger


class UnitValue(Decimal):
    """Unit Value"""

    def __format__(self, spec):
        value = Decimal(self)
        formatDict = parseSpec(spec)

        systems = formatDict["type"] or ""

        if systems and all(s.casefold() in self._systems.keys() for s in systems):
            accuracy = formatDict["precision"] or 2
            accuracy = int(accuracy)
            useFractional = formatDict["fractional"] == "%"
            formatDict["type"] = None
            formatDict["precision"] = None
            numspec = buildSpec(formatDict)

            formattedUnits = []
            for s in systems:
                preferName = s.upper() == s
                system = self._systems[s.casefold()]
                unit = system.getBestUnit(value)
                formattedUnits.append(unit.format(value, accuracy, numspec, preferName, useFractional))

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
        unit = cls._units.get(unitStr, None)
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
        Unit(symbol="in", factor=inch, name="inch", namePlural="inches", symbols=["\""], fractional=True),
        Unit(symbol="ft", factor=foot, name="foot", namePlural="feet", symbols=["'"]),
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
        Unit(factor=Decimal("0.122682"), name="can of soda", namePlural="cans of soda", names=["can", "cans"]),
        Unit(factor=Decimal("0.2921"), name="Barbie", namePlural="Barbies", names=["doll", "dolls"]),
        Unit(factor=Decimal("0.000352778"), symbol="pt", name="font point", namePlural="font points"),
        Unit(factor=Decimal("0.1905"), name="pencil", namePlural="pencils", names=["pen", "pens"]),
        Unit(factor=Decimal("4.3"), name="story", namePlural="stories"),
        Unit(factor=Decimal("0.00005"), name="human hair", namePlural="hair widths", names=["hair"]),
        Unit(factor=Decimal("109.728"), name="football field", namePlural="football fields", names=["field", "fields"]),
        Unit(factor=Decimal("0.015"), name="keyboard key", namePlural="keyboard keys"),
        Unit(factor=Decimal("0.045"), name="door key", namePlural="door keys", names=["key", "keys"]),
        Unit(factor=Decimal("0.015"), name="fruit loop", namePlural="fruit loops"),
        Unit(factor=Decimal("0.0508"), name="hairpin", namePlural="hairpins", names=["bobby pin", "bobby pins"]),
        Unit(factor=Decimal("0.076"), name="Q-tip", namePlural="Q-tips", names=["cotton swab", "swab", "cotton swabs", "swabs"]),
        Unit(factor=Decimal("0.1778"), name="toothbrush", namePlural="toothbrushes"),
        Unit(factor=Decimal("0.0762"), name="Post-it note", namePlural="Post-it notes"),
        Unit(factor=Decimal("0.02"), name="dice", names=["die"]),
        Unit(factor=Decimal("0.049784"), name="AA battery", namePlural="AA batteries", names=["battery", "batteries"]),
        Unit(factor=Decimal("0.034925"), name="paperclip", namePlural="paperclips"),
        Unit(factor=Decimal("0.01"), name="staple", namePlural="staples"),
        Unit(factor=Decimal("0.029718"), name="bottlecap", namePlural="bottlecaps", names=["cap", "caps"]),
        Unit(factor=Decimal("80"), name="city block", namePlural="city blocks", names=["block", "blocks"]),
        Unit(factor=Decimal("0.053"), name="bullet vibe", namePlural="bullet vibes"),
        Unit(factor=Decimal("13.716"), name="city bus", namePlural="city buses", names=["bus", "buses"]),
        Unit(factor=Decimal("16.1798"), name="train car", namePlural="train cars"),
        Unit(factor=Decimal("70.7136"), name="boeing 747", namePlural="Boeing 747s", names=["747", "747s"]),
        Unit(factor=Decimal("360"), name="cruise ship", namePlural="cruise ships"),
        Unit(factor=Decimal("6"), name="2-lane road width", namePlural="2-lane road widths", names=["road width", "road widths"]),
        Unit(factor=Decimal("1.2192"), name="sidewalk width", namePlural="sidewalk widths"),
        Unit(factor=Decimal("0.0001"), name="thickness of a sheet of paper", namePlural="thicknesses of a sheet of paper"),
        Unit(factor=Decimal("93"), name="statue of liberty", namePlural="Statue of Libertys", names=["lady liberty", "lady libertys", "lady liberties", "statue of liberties"]),
        Unit(factor=Decimal("70"), name="falcon heavy", namePlural="Falcon Heavys", names=["rocket", "rockets"]),
        Unit(factor=Decimal("0.092075"), name="crayon", namePlural="crayons"),
        Unit(factor=Decimal("0.01905"), name="scotch tape width", namePlural="Scotch tape widths", names=["tape width", "tape widths"]),
        Unit(factor=Decimal("0.049"), name="duct tape width", namePlural="duct tape widths"),
        Unit(factor=Decimal("0.11"), name="lightbulb", namePlural="lightbulbs"),
        Unit(factor=Decimal("0.038"), name="tea light", namePlural="tea lights"),
        Unit(factor=Decimal("0.23"), name="chopstick", namePlural="chopsticks"),
        Unit(factor=Decimal("0.028575"), name="safety pin", namePlural="safety pins"),
        Unit(factor=Decimal("0.0762"), name="band-aid", namePlural="band-aids", names=["bandage", "bandages"]),
        Unit(factor=Decimal("0.060325"), name="Zippo lighter", namePlural="Zippo lighters", names=["lighter", "lighters"]),
        Unit(factor=Decimal("0.1005"), name="audio cassette", namePlural="audio cassettes", names=["cassette", "cassettes"]),
        Unit(factor=Decimal("0.187"), name="VHS tape", namePlural="VHS tapes", names=["video tape", "video tapes"]),
        Unit(factor=Decimal("0.12"), name="CD", namePlural="CDs"),
        Unit(factor=Decimal("0.032"), name="SD card", namePlural="SD cards"),
        Unit(factor=Decimal("0.015"), name="MicroSD card", namePlural="MicroSD cards"),
        Unit(factor=Decimal("0.06"), name="egg", namePlural="eggs"),
        Unit(factor=Decimal("443.1792"), name="Empire State Building", namePlural="Empire State Buildings"),
        Unit(factor=Decimal("0.864"), name="doorknob height", namePlural="doorknob heights"),
        Unit(factor=Decimal("0.9652"), name="guitar length", namePlural="guitar lengths", names=["guitar", "guitars"]),
        Unit(factor=Decimal("2.032"), name="doorway height", namePlural="doorway heights", names=["doorway", "doorways"]),
        Unit(factor=Decimal("0.9144"), name="countertop height", namePlural="countertop heights"),
        Unit(factor=Decimal("1.7399"), name="fridge height", namePlural="fridge heights", names=["fridge", "fridges"]),
        Unit(factor=Decimal("2.032"), name="bed length", namePlural="bed lengths", names=["bed", "beds"]),
        Unit(factor=Decimal("0.1056386"), name="juice box", namePlural="juice boxes"),
        Unit(factor=Decimal("0.095"), name="coffee mug", namePlural="coffee mugs", names=["mug", "mugs"]),
        Unit(factor=Decimal("0.0745"), name="baseball", namePlural="baseballs"),
        Unit(factor=Decimal("0.240538"), name="basketball", namePlural="basketballs"),
        Unit(factor=Decimal("0.04267"), name="golf ball", namePlural="golf balls"),
        Unit(factor=Decimal("0.22"), name="soccer ball", namePlural="soccer balls", names=["football", "footballs"]),
        Unit(factor=Decimal("324.0024"), name="Eiffel Tower", namePlural="Eiffel Towers", names=["eiffel", "eiffels"]),
        Unit(factor=Decimal("0.034"), name="pin", namePlural="pins", names=["needle", "needles", "sewing needle", "dewing needles"]),
        Unit(factor=Decimal("0.002"), name="pinhead", namePlural="pinheads"),
        Unit(factor=Decimal("0.01"), name="ant", namePlural="ants"),
        Unit(factor=Decimal("0.006"), name="grain of rice", namePlural="grains of rice", names=["rive grains", "rive grain", "grain", "grains", "rice"]),
        Unit(factor=Decimal("0.057"), name="Rubik's cube", namePlural="Rubik's cubes"),
        Unit(factor=Decimal("0.075"), name="apple", namePlural="apples"),
        Unit(factor=Decimal("0.1905"), name="banana", namePlural="bananas"),
        Unit(factor=Decimal("1.4351"), name="railway track width", namePlural="railway track widths"),
        Unit(factor=Decimal("0.508"), name="beach ball", namePlural="beach balls"),
        Unit(factor=Decimal("56.6928"), name="Leaning Tower of Pisa", namePlural="Leaning Tower of Pisas"),
        Unit(factor=Decimal("96.012"), name="Big Ben", namePlural="Big Bens"),
        Unit(factor=Decimal("0.0096"), name="lego brick", namePlural="lego bricks", names=["lego", "legos"]),
        Unit(factor=Decimal("0.04"), name="lego minifig", namePlural="lego minifigs", names=["minifig", "minifigs"]),
        Unit(factor=Decimal("12742000"), name="Earth", namePlural="Earths"),
        Unit(factor=Decimal("1391000000"), name="Sun", namePlural="Suns"),
        Unit(factor=Decimal("3474200"), name="moon", namePlural="moons"),
        Unit(factor=Decimal("0.10795"), name="Solo cup", namePlural="Solo cups", names=["cup", "cups"]),
        Unit(factor=Decimal("3.5052"), name="light pole", namePlural="light poles"),
        Unit(factor=Decimal("0.2794"), name="letter paper", namePlural="letter papers", names=["paper", "papers"]),
        Unit(factor=Decimal("0.001"), name="grain of sand", namePlural="grains of sand", names=["sand"]),
        Unit(factor=Decimal("0.002"), name="drop of water", namePlural="drops of water", names=["water drops", "water drop", "drop", "drops"]),
        Unit(factor=Decimal("50"), name="swimming pool", namePlural="swimming pools", names=["pool", "pools"]),
        Unit(factor=Decimal("0.02426"), name="quarter", namePlural="quarters"),
        Unit(factor=Decimal("0.01905"), name="penny", namePlural="pennies"),
        Unit(factor=Decimal("0.01791"), name="dime", namePlural="dimes"),
        Unit(factor=Decimal("0.3"), name="vinyl record", namePlural="vinyl records", names=["record", "records"]),
        Unit(factor=Decimal("0.1905"), name="stair", namePlural="stairs"),
        Unit(factor=Decimal("0.762"), name="fire hydrant", namePlural="fire hydrants", names=["hydrant", "hydrants"])
    ])
    # SV systems
    _systems = {
        "m": SystemRegistry(_units, [
            SystemUnit("ym"),
            SystemUnit("zm"),
            SystemUnit("am"),
            SystemUnit("fm"),
            SystemUnit("pm"),
            SystemUnit("nm"),
            SystemUnit("µm"),
            SystemUnit("mm", trigger=Decimal("1e-4")),
            SystemUnit("cm"),
            SystemUnit("m"),
            SystemUnit("km"),
            SystemUnit("Mm", trigger=Decimal("1e-7")),
            SystemUnit("Gm"),
            SystemUnit("Tm"),
            SystemUnit("Pm"),
            SystemUnit("Em"),
            SystemUnit("Zm"),
            SystemUnit("Ym"),
            SystemUnit("uni"),
            SystemUnit("kuni"),
            SystemUnit("Muni"),
            SystemUnit("Guni"),
            SystemUnit("Tuni"),
            SystemUnit("Puni"),
            SystemUnit("Euni"),
            SystemUnit("Zuni"),
            SystemUnit("Yuni"),
            SystemUnit("∞")
        ]),
        "u": SystemRegistry(_units, [
            SystemUnit("ym"),
            SystemUnit("zm"),
            SystemUnit("am"),
            SystemUnit("fm"),
            SystemUnit("pm"),
            SystemUnit("nm"),
            SystemUnit("µm"),
            SystemUnit("mm", trigger=Decimal("1e-4")),
            SystemUnit("in", trigger=inch / Decimal("10")),
            SystemUnit(("'", "\"")),
            SystemUnit("mi"),
            SystemUnit("AU"),
            SystemUnit("ly"),
            SystemUnit("uni"),
            SystemUnit("kuni"),
            SystemUnit("Muni"),
            SystemUnit("Guni"),
            SystemUnit("Tuni"),
            SystemUnit("Puni"),
            SystemUnit("Euni"),
            SystemUnit("Zuni"),
            SystemUnit("Yuni"),
            SystemUnit("∞")
        ]),
        "o": SystemRegistry(_units, [
            SystemUnit("credit card"),
            SystemUnit("can of soda"),
            SystemUnit("Barbie"),
            SystemUnit("font point"),
            SystemUnit("pencil"),
            SystemUnit("story"),
            SystemUnit("human hair"),
            SystemUnit("football field"),
            SystemUnit("keyboard key"),
            SystemUnit("door key"),
            SystemUnit("fruit loop"),
            SystemUnit("hairpin"),
            SystemUnit("Q-tip"),
            SystemUnit("toothbrush"),
            SystemUnit("Post-it note"),
            SystemUnit("dice"),
            SystemUnit("AA battery"),
            SystemUnit("paperclip"),
            SystemUnit("staple"),
            SystemUnit("bottlecap"),
            SystemUnit("city block"),
            SystemUnit("bullet vibe"),
            SystemUnit("city bus"),
            SystemUnit("train car"),
            SystemUnit("boeing 747"),
            SystemUnit("cruise ship"),
            SystemUnit("2-lane road width"),
            SystemUnit("sidewalk width"),
            SystemUnit("thickness of a sheet of paper"),
            SystemUnit("statue of liberty"),
            SystemUnit("falcon heavy"),
            SystemUnit("crayon"),
            SystemUnit("scotch tape width"),
            SystemUnit("duct tape width"),
            SystemUnit("lightbulb"),
            SystemUnit("tea light"),
            SystemUnit("chopstick"),
            SystemUnit("safety pin"),
            SystemUnit("band-aid"),
            SystemUnit("Zippo lighter"),
            SystemUnit("audio cassette"),
            SystemUnit("VHS tape"),
            SystemUnit("CD"),
            SystemUnit("SD card"),
            SystemUnit("MicroSD card"),
            SystemUnit("egg"),
            SystemUnit("Empire State Building"),
            SystemUnit("doorknob height"),
            SystemUnit("guitar lengths"),
            SystemUnit("doorway height"),
            SystemUnit("countertop height"),
            SystemUnit("fridge height"),
            SystemUnit("bed length"),
            SystemUnit("juice box"),
            SystemUnit("coffee mug"),
            SystemUnit("baseball"),
            SystemUnit("basketball"),
            SystemUnit("golf ball"),
            SystemUnit("soccer ball"),
            SystemUnit("Eiffel Tower"),
            SystemUnit("pin"),
            SystemUnit("pinhead"),
            SystemUnit("ant"),
            SystemUnit("grain of rice"),
            SystemUnit("Rubik's cube"),
            SystemUnit("apple"),
            SystemUnit("banana"),
            SystemUnit("railway track width"),
            SystemUnit("beach ball"),
            SystemUnit("Leaning Tower of Pisa"),
            SystemUnit("Big Ben"),
            SystemUnit("lego brick"),
            SystemUnit("lego minifig"),
            SystemUnit("Earth"),
            SystemUnit("Sun"),
            SystemUnit("moon"),
            SystemUnit("Solo cup"),
            SystemUnit("light pole"),
            SystemUnit("letter paper"),
            SystemUnit("grain of sand"),
            SystemUnit("drop of water"),
            SystemUnit("swimming pool"),
            SystemUnit("quarter"),
            SystemUnit("penny"),
            SystemUnit("dime"),
            SystemUnit("vinyl record"),
            SystemUnit("stair"),
            SystemUnit("hydrant")
        ])
    }

    @classmethod
    def getUnitValuePair(cls, s):
        s = removeBrackets(s)
        s = cls.isFeetAndInchesAndIfSoFixIt(s)
        match = re.search(r"(?P<value>[\-+]?\d+\.?\d*) *(?P<unit>[a-zA-Z\'\" ]+)", s)
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
        Unit(factor=Decimal("1e-24"), symbol="yg", name="yoctogram", namePlural="yoctograms"),
        Unit(factor=Decimal("1e-21"), symbol="zg", name="zeptogram", namePlural="zeptograms"),
        Unit(factor=Decimal("1e-18"), symbol="ag", name="attogram", namePlural="attograms"),
        Unit(factor=Decimal("1e-15"), symbol="fg", name="femtogram", namePlural="femtograms"),
        Unit(factor=Decimal("1e-12"), symbol="pg", name="picogram", namePlural="picograms"),
        Unit(factor=Decimal("1e-9"), symbol="ng", name="nanogram", namePlural="nanograms"),
        Unit(factor=Decimal("1e-6"), symbol="µg", name="microgram", namePlural="micrograms"),
        Unit(factor=Decimal("1e-3"), symbol="mg", name="milligram", namePlural="milligrams"),
        Unit(factor=Decimal("1e0"), symbol="g", name="gram", namePlural="grams"),
        Unit(factor=ounce, symbol="oz", name="kilogram", namePlural="kilograms"),
        Unit(factor=pound, symbol="lb", name="pound", namePlural="pounds", symbols=["lbs"]),
        Unit(factor=Decimal("1e3"), symbol="kg", name="kilogram", namePlural="kilograms"),
        Unit(factor=uston, name="US tons"),
        Unit(factor=Decimal("1e6"), symbol="t", name="megagram", namePlural="megagrams", names=["ton", "tons", "tonne", "tonnes"]),
        Unit(factor=Decimal("1e9"), symbol="kt", name="gigagram", namePlural="gigagrams", names=["kilotons", "kiloton", "kilotonnes", "kilotonne"]),
        Unit(factor=Decimal("1e12"), symbol="Mt", name="teragram", namePlural="teragrams", names=["megatons", "megaton", "megatonnes", "megatonne"]),
        Unit(factor=Decimal("1e15"), symbol="Gt", name="petagram", namePlural="petagrams", names=["gigatons", "gigaton", "gigatonnes", "gigatonne"]),
        Unit(factor=Decimal("1e18"), symbol="Tt", name="exagram", namePlural="exagrams", names=["teratons", "teraton", "teratonnes", "teratonne"]),
        Unit(factor=Decimal("1e21"), symbol="Pt", name="zettagram", namePlural="zettagrams", names=["petatons", "petaton", "petatonnes", "petatonne"]),
        Unit(factor=Decimal("1e24"), symbol="Et", name="yottagram", namePlural="yottagrams", names=["exatons", "exaton", "exatonnes", "exatonne"]),
        Unit(factor=Decimal("1e27"), symbol="Zt", name="zettaton", namePlural="zettatons", names=["zettatonnes", "zettatonne"]),
        Unit(factor=earth, name="Earth", namePlural="Earths"),
        Unit(factor=Decimal("1e30"), symbol="Yt", name="yottaton", namePlural="yottatons", names=["yottatonnes", "yottatonne"]),
        Unit(factor=sun, name="Sun", namePlural="Suns"),
        Unit(factor=milkyway, name="Milky Ways"),
        Unit(factor=uniWV * Decimal("1e0"), symbol="uni", name="universe", namePlural="universes"),
        Unit(factor=uniWV * Decimal("1e3"), symbol="kuni", name="kilouniverse", namePlural="kilouniverses"),
        Unit(factor=uniWV * Decimal("1e6"), symbol="Muni", name="megauniverse", namePlural="megauniverses"),
        Unit(factor=uniWV * Decimal("1e9"), symbol="Guni", name="gigauniverse", namePlural="gigauniverses"),
        Unit(factor=uniWV * Decimal("1e12"), symbol="Tuni", name="terauniverse", namePlural="terauniverses"),
        Unit(factor=uniWV * Decimal("1e15"), symbol="Puni", name="petauniverse", namePlural="petauniverses"),
        Unit(factor=uniWV * Decimal("1e18"), symbol="Euni", name="exauniverse", namePlural="exauniverses"),
        Unit(factor=uniWV * Decimal("1e21"), symbol="Zuni", name="zettauniverse", namePlural="zettauniverses"),
        Unit(factor=uniWV * Decimal("1e24"), symbol="Yuni", name="yottauniverse", namePlural="yottauniverses"),
        FixedUnit(factor=Decimal(infinity), symbol="∞", name="infinity", names=["infinite"])
    ])
    # WV systems
    _systems = {
        "m": SystemRegistry(_units, [
            SystemUnit("yg"),
            SystemUnit("zg"),
            SystemUnit("ag"),
            SystemUnit("fg"),
            SystemUnit("pg"),
            SystemUnit("ng"),
            SystemUnit("µg"),
            SystemUnit("mg"),
            SystemUnit("g"),
            SystemUnit("kg"),
            SystemUnit("t"),
            SystemUnit("kt"),
            SystemUnit("Mt"),
            SystemUnit("Gt"),
            SystemUnit("Tt"),
            SystemUnit("Pt"),
            SystemUnit("Et"),
            SystemUnit("Zt"),
            SystemUnit("Yt"),
            SystemUnit("uni"),
            SystemUnit("kuni"),
            SystemUnit("Muni"),
            SystemUnit("Guni"),
            SystemUnit("Tuni"),
            SystemUnit("Puni"),
            SystemUnit("Euni"),
            SystemUnit("Zuni"),
            SystemUnit("Yuni"),
            SystemUnit("∞"),
        ]),
        "u": SystemRegistry(_units, [
            SystemUnit("yg"),
            SystemUnit("zg"),
            SystemUnit("ag"),
            SystemUnit("fg"),
            SystemUnit("pg"),
            SystemUnit("ng"),
            SystemUnit("µg"),
            SystemUnit("mg"),
            SystemUnit("g"),
            SystemUnit("oz"),
            SystemUnit("lb"),
            SystemUnit(" US tons"),
            SystemUnit("earths"),
            SystemUnit("sun"),
            SystemUnit(" Milky Ways"),
            SystemUnit("uni"),
            SystemUnit("kuni"),
            SystemUnit("Muni"),
            SystemUnit("Guni"),
            SystemUnit("Tuni"),
            SystemUnit("Puni"),
            SystemUnit("Euni"),
            SystemUnit("Zuni"),
            SystemUnit("Yuni"),
            SystemUnit("∞"),
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

    def __repr__(self):
        return f"WV('{self}')"


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
        Unit(name="month", namePlural="months", factor=month),
        Unit(symbol="y", name="year", namePlural="years", factor=year, symbols=["a", "yr"])
    ])
    _systems = {
        "m": SystemRegistry(_units, [
            SystemUnit("seconds"),
            SystemUnit("minutes"),
            SystemUnit("hours"),
            SystemUnit("days"),
            SystemUnit("weeks"),
            SystemUnit("months"),
            SystemUnit("years")
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

    def __repr__(self):
        return f"TV('{self}')"
