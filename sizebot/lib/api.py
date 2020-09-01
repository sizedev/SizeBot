from sizebot.lib import userdb
from sizebot.lib.errors import UserNotFoundException


def getSizebotUser(guildid, userid):
    try:
        u = userdb.load(guildid, userid)
    except UserNotFoundException:
        return None
    return u.nickname
