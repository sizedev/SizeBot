import logging

import arrow

import discord
from sizebot.lib import errors, userdb

logger = logging.getLogger("sizebot")


async def on_message(m):
    """Is this user active?"""
    if m.author.bot:
        return
    if not isinstance(m.author, discord.Member):
        return
    try:
        userdata = userdb.load(m.guild.id, m.author.id)
    except errors.UserNotFoundException:
        return
    userdata.lastactive = arrow.now()
    userdb.save(userdata)
