from discord import User, Member

from sizebot.lib import errors, userdb

MAX_NICK_LEN = 32


def _generate_suffix(sizetag: str, species: str | None = None) -> str:
    """Generate a nickname suffix"""
    suffix = f" [{sizetag}]"
    if species:
        suffix = f" [{sizetag}, {species}]"
    return suffix


def _generate_nickname(nick: str, sizetag: str, species: str | None = None, cropnick: bool = False) -> str | None:
    """Generate a valid nickname (if possible)"""
    suffix = _generate_suffix(sizetag, species)
    newnick = nick + suffix

    if cropnick and len(newnick) > MAX_NICK_LEN:
        suffix = "…" + suffix
        short_nick = nick[:MAX_NICK_LEN - len(suffix)]
        if len(short_nick) < 3:
            return None
        newnick = short_nick + suffix

    if len(newnick) > MAX_NICK_LEN:
        return None

    return newnick


def _can_edit_nick(user: User | Member) -> bool:
    """Determine if the bot is able to edit this user's nickname"""
    # Don't try updating nick when user is None
    if user is None:
        return False
    # Don't try updating nicks of webhooks
    if user.discriminator == "0000":
        return False
    # Don't trying updating nicks outside of a guild
    if not isinstance(user, Member):
        return False
    # Don't try updating nicks of bots
    if user.bot:
        return False
    # Don't try updating nicks of guild owners
    if user.id == user.guild.owner_id:
        return False
    # Don't try updating nicks on servers where Manage Nicknames permission is missing
    if not user.guild.me.guild_permissions.manage_nicknames:
        return False
    # Don't try updating nicks with roles higher than the bot roles
    if not user.guild.me.top_role.position > user.top_role.position:
        return False
    return True


async def nick_update(user: User | Member):
    """Update users nicknames to include sizetags"""
    if not _can_edit_nick(user):
        return

    try:
        userdata = userdb.load(user.guild.id, user.id)
    except errors.UserNotFoundException:
        return

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    sizetag = format(userdata.height, f",{userdata.unitsystem}%")

    newnick = (
        _generate_nickname(userdata.nickname, sizetag, userdata.species)
        or _generate_nickname(userdata.nickname, sizetag)
        or _generate_nickname(userdata.nickname, sizetag, cropnick=True)
        or userdata.nickname[:MAX_NICK_LEN]
    )

    await user.edit(nick = newnick)


async def nick_reset(user: User | Member):
    """Remove sizetag from user's nickname"""
    if not _can_edit_nick(user):
        return

    userdata = userdb.load(user.guild.id, user.id, allow_unreg=True)

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    await user.edit(nick = userdata.nickname)
