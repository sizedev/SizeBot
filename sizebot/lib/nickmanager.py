import discord

from sizebot.lib import errors, userdb
from sizebot.lib.utils import glitch_string

MAX_NICK_LEN = 32


def generate_suffix(sizetag, species=None):
    suffix = f" [{sizetag}]"
    if species:
        suffix = f" [{sizetag}, {species}]"
    return suffix


# Generate a valid nickname (if possible)
def generate_nickname(nick, sizetag, species=None, cropnick=False):
    suffix = generate_suffix(sizetag, species)
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


# TODO: Deal with not being able to change nicks of roles above the bot.
# Update users nicknames to include sizetags
async def nick_update(user):
    # Don't try updating nicks on servers where Manage Nicknames permission is missing
    if not user.guild.me.guild_permissions.manage_nicknames:
        return

    # webhooks
    if user.discriminator == "0000":
        return
    # non-guild messages
    if not isinstance(user, discord.Member):
        return
    # bots
    if user.bot:
        return
    # guild owner
    if user.id == user.guild.owner_id:
        return

    try:
        userdata = userdb.load(user.guild.id, user.id)
    except errors.UserNotFoundException:
        return

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    height = userdata.height
    if height is None:
        height = userdata.baseheight
    nick = userdata.nickname[:MAX_NICK_LEN]
    species = userdata.species

    sizetag = ""
    if userdata.unitsystem in ["m", "u", "o"]:
        sizetag = format(height, f",{userdata.unitsystem}%")

    if userdata.incomprehensible:
        glitch = "█▓▒░　"
        if species is not None:
            species = glitch_string(species, charset = glitch)
        if sizetag is not None:
            sizetag = glitch_string(sizetag, charset = glitch)

    newnick = (
        generate_nickname(nick, sizetag, species)
        or generate_nickname(nick, sizetag)
        or generate_nickname(nick, sizetag, cropnick=True)
        or nick
    )

    try:
        # PERMISSION: requires manage_nicknames
        await user.edit(nick = newnick)
    except discord.Forbidden:
        raise errors.NoPermissionsException


async def nickReset(user):
    """Remove sizetag from user's nickname"""
    # webhooks
    if user.discriminator == "0000":
        return
    # non-guild messages
    if not isinstance(user, discord.Member):
        return
    # bots
    if user.bot:
        return
    # guild owner
    if user.id == user.guild.owner_id:
        return

    userdata = userdb.load(user.guild.id, user.id, allow_unreg=True)

    # User's display setting is N. No sizetag.
    if not userdata.display:
        return

    try:
        # PERMISSION: requires manage_nicknames
        await user.edit(nick = userdata.nickname)
    except discord.Forbidden:
        raise errors.NoPermissionsException
