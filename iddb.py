import io

import conf


def loadIds():
    # IDs are stored in text/ids.txt.
    # The format is one ID per line, in the form {id}:{name}
    # This file is not tracked by Git.
    with io.open(conf.idfilepath, "r", encoding = "utf-8") as idfile:
        ids = {name: id for id, name in [line.rstrip().split(":", 1) for line in idfile]}
    return ids


def getID(name):
    ids = loadIds()
    return ids.get(name, 000000000000000000)
