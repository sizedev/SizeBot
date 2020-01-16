import discord
from discord.ext import commands


from sizebot import conf
from sizebot.lib import errors


def requireAdmin(ctx):
    if ctx.author.id not in conf.admins:
        raise commands.CommandInvokeError(errors.AdminPermissionException())
    return True


def denyGuildBan(ctx):
    member = ctx.author
    isMember = isinstance(member, discord.Member)
    if not isMember:
        return True
    isGuildBanned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
    return not isGuildBanned
