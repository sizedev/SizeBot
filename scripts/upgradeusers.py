from sizebot.lib.decimal import Decimal
from sizebot.lib import userdb

# Deprecated user array constants
NICK = 0
DISP = 1
CHEI = 2
BHEI = 3
BWEI = 4
DENS = 5
UNIT = 6
SPEC = 7


def loadLegacy(id):
    """Load a user from the old file format"""
    with open(userdb.userdbpath / f"{id}.txt", "r") as f:
        # Make array of lines from file.
        lines = f.read().splitlines()
    lines = [line.strip() for line in lines]

    userdata = userdb.User()
    userdata.id = id
    userdata.nickname = lines[NICK]
    userdata.display = lines[DISP]
    if lines[CHEI] != "None":
        userdata.height = lines[CHEI]
        userdata.height /= Decimal("1e6")
    if lines[BHEI] != "None":
        userdata.baseheight = lines[BHEI]
        userdata.baseheight /= Decimal("1e6")
    if lines[BWEI] != "None":
        userdata.baseweight = lines[BWEI] * lines[DENS]     # Drop density, and instead update base weight to match
        userdata.baseweight /= Decimal("1e3")
    userdata.unitsystem = lines[UNIT]
    if lines[SPEC] != "None":
        userdata.species = lines[SPEC]

    return userdata


def upgradeusers():
    print(f"Looking for user files in {userdb.userdbpath}")
    filepaths = list(userdb.userdbpath.glob("*.txt"))
    print(f"Found {len(filepaths)} users")
    for filepath in filepaths:
        id = filepath.stem
        print(f"Loading legacy user file for {id}")
        userdata = loadLegacy(id)
        print(f"Saving new user file for {id}")
        userdb.save(userdata)


if __name__ == "__main__":
    upgradeusers()
