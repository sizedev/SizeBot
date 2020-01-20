import discord
from discord.ext import commands


from sizebot import conf
from sizebot.lib import errors


def requireAdmin(ctx):
    if ctx.author.id not in conf.admins:
        raise commands.CommandInvokeError(errors.AdminPermissionException())
    return True
