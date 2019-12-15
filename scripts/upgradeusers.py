import userdb
from userdb import NICK, DISP, CHEI, BHEI, BWEI, DENS, UNIT, SPEC, User


# Load a user from the old file format
def loadLegacy(id):
    with open(userdb.userdbpath / f"{id}.txt", "r") as f:
        # Make array of lines from file.
        lines = f.read().splitlines()
    lines = [line.strip() for line in lines]

    userdata = User()
    userdata.id = id
    userdata.nickname = lines[NICK]
    userdata.display = lines[DISP]
    if lines[CHEI] != "None":
        userdata.height = lines[CHEI]
        userdata.height /= 10**6
    if lines[BHEI] != "None":
        userdata.baseheight = lines[BHEI]
        userdata.baseheight /= 10**6
    if lines[BWEI] != "None":
        userdata.baseweight = lines[BWEI]
        userdata.baseweight /= 10**3
    if lines[DENS] != "None":
        userdata.density = lines[DENS]
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
