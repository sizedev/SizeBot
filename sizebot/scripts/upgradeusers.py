import asyncio
from pathlib import Path

from sizebot.lib.decimal import Decimal
from sizebot.lib import units, userdb

# Deprecated user array constants
NICK = 0
DISP = 1
CHEI = 2
BHEI = 3
BWEI = 4
DENS = 5
UNIT = 6
SPEC = 7

units.init()


class BadLegacyUser(Exception):
    pass


def loadLegacy(path):
    """Load a user from the old file format"""
    with open(path, "r", encoding = "utf-8") as f:
        # Make array of lines from file.
        lines = f.read().splitlines()
    lines = [line.strip() for line in lines]
    if len(lines) < 8:
        raise BadLegacyUser(f"Bad legacy user file: {path}")
    uid = path.stem

    userdata = userdb.User()
    userdata.guildid = 350429009730994199
    userdata.id = uid
    userdata.nickname = lines[NICK]
    userdata.display = False if lines[DISP].lower() == "n" else True
    if lines[CHEI] != "None":
        userdata.height = Decimal(lines[CHEI])
        userdata.height /= Decimal("1e6")
    if lines[BHEI] != "None":
        userdata.baseheight = Decimal(lines[BHEI])
        userdata.baseheight /= Decimal("1e6")
    if lines[BWEI] != "None":
        userdata.baseweight = Decimal(lines[BWEI]) * Decimal(lines[DENS])  # Drop density, and instead update base weight to match
        userdata.baseweight /= Decimal("1e3")
    userdata.unitsystem = lines[UNIT]
    if lines[SPEC] != "None":
        userdata.species = lines[SPEC]

    return userdata


def upgradeusers(path):
    print(f"Looking for user files in {path}")
    filepaths = list(path.glob("*.txt"))
    print(f"Found {len(filepaths)} users")
    imported = 0
    for filepath in filepaths:
        try:
            userdata = loadLegacy(filepath)
        except BadLegacyUser as e:
            print(e)
            continue
        userdb.save(userdata)
        imported += 1
    print(f"Successfully imported {imported} users")


def main():
    upgradeusers(Path("."))


if __name__ == "__main__":
    main()
