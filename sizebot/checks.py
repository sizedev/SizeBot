from discord.ext import commands

from sizebot.conf import conf
from sizebot import digierror as errors


def requireAdmin(ctx):
    if ctx.message.author.id not in conf.admins:
        raise commands.CommandInvokeError(errors.AdminPermissionException())
    return True
