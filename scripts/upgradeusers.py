import userdb
from userdb import NICK, DISP, CHEI, BHEI, BWEI, DENS, UNIT, SPEC, User


# Load a user from the old file format
def loadLegacy(id):
    with open(userdb.userdbpath / f"{id}.txt", "r") as f:
        # Make array of lines from file.
        lines = f.read().splitlines()
    lines = [line.strip() for line in lines]

    user = User()
    user.id = id
    user.nickname = lines[NICK]
    user.display = lines[DISP]
    if lines[CHEI] != "None":
        user.height = lines[CHEI]
        user.height
    if lines[BHEI] != "None":
        user.baseheight = lines[BHEI]
    if lines[BWEI] != "None":
        user.baseweight = lines[BWEI]
    if lines[DENS] != "None":
        user.density = lines[DENS]
    user.unitsystem = lines[UNIT]
    if lines[SPEC] != "None":
        user.species = lines[SPEC]

    return user


def upgradeusers():
    print(f"Looking for user files in {userdb.userdbpath}")
    filepaths = list(userdb.userdbpath.glob("*.txt"))
    print(f"Found {len(filepaths)} users")
    for filepath in filepaths:
        id = filepath.stem
        print(f"Loading legacy user file for {id}")
        user = loadLegacy(id)
        print(f"Saving new user file for {id}")
        userdb.save(user)


if __name__ == "__main__":
    upgradeusers()
