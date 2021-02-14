import discord

from sizebot.lib import errors, userdb


# TODO: Move to somewhere other than here.
# TODO: Deal with not being able to change nicks of roles above the bot.
# Update users nicknames to include sizetags
async def nickUpdate(user):
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
    nick = userdata.nickname
    species = userdata.species

    if userdata.unitsystem in ["m", "u", "o"]:
        sizetag = format(height, f",{userdata.unitsystem}%")
    else:
        sizetag = ""

    if species is not None:
        sizetag = f"{sizetag}, {species}"

    max_nick_len = 32

    if len(nick) > max_nick_len:
        # Truncate nick is too long
        nick = nick[:max_nick_len]

    if len(nick) + len(sizetag) + 3 <= max_nick_len:
        # Fit full nick and sizetag
        newnick = f"{nick} [{sizetag}]"
    elif len(sizetag) + 7 <= max_nick_len:
        # Fit short nick and sizetag
        chars_left = max_nick_len - len(sizetag) - 4
        short_nick = nick[:chars_left]
        newnick = f"{short_nick}… [{sizetag}]"
    else:
        # Cannot fit the new sizetag
        newnick = nick
    try:
        # PERMISSION: requires manage_nicknames
        await user.edit(nick = newnick)
    except discord.Forbidden:
        raise errors.NoPermissionsException


# TODO: Move to somewhere other than here.
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
