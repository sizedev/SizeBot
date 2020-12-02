import importlib.resources as pkg_resources
import logging
import json

import sizebot.data
from sizebot.lib import utils

modelJSON = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))


# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    level = logging.WARNING

    def formatMessage(self):
        return None

    def formatUserMessage(self):
        return None

    def __repr__(self):
        return utils.getFullname(self)

    def __str__(self):
        return self.formatMessage() or repr(self)


class DigiContextException(Exception):
    level = logging.WARNING

    async def formatMessage(self, ctx):
        return None

    async def formatUserMessage(self, ctx):
        return None

    def __repr__(self):
        return utils.getFullname(self)

    def __str__(self):
        return repr(self)


class UserNotFoundException(DigiContextException):
    def __init__(self, guildid, userid):
        self.guildid = guildid
        self.userid = userid

    async def formatMessage(self, ctx):
        user = await ctx.guild.fetch_member(self.userid)
        usernick = user.display_name
        guild = await ctx.bot.fetch_guild(self.guildid)
        return f"User {self.userid} ({usernick}) not found in {self.guildid} ({guild.name})."

    async def formatUserMessage(self, ctx):
        user = await ctx.guild.fetch_member(self.userid)
        usernick = user.display_name
        return (
            f"Sorry, {usernick} isn't registered with SizeBot.\n"
            "To register, use the `&register` command.")


class GuildNotFoundException(DigiException):
    def __init__(self, guildid):
        self.guildid = guildid

    async def formatMessage(self):
        return f"Guild {self.guildid} not found."


class ValueIsZeroException(DigiException):
    def formatMessage(self):
        return "Value zero received when unexpected."

    def formatUserMessage(self):
        return (
            "Nice try.\n"
            "You can't change by a value of zero.")


class ValueIsOneException(DigiException):
    def formatMessage(self):
        return "Value one received when unexpected."

    def formatUserMessage(self):
        return (
            "Nice try.\n"
            "You can't change by a value of one.\n"
            "The reason for this is that it doesn't do anything, "
            "and this is a waste of memory and processing power for SizeBot, "
            "especially if the task is a repeating one.")


class ChangeMethodInvalidException(DigiContextException):
    def __init__(self, changemethod):
        self.changemethod = changemethod

    async def formatUserMessage(self, ctx):
        usernick = ctx.author.display_name
        return f"Sorry, {usernick}! {self.changemethod} is not a valid change method."


class CannotSaveWithoutIDException(DigiException):
    level = logging.CRITICAL

    def formatMessage(self):
        return "Tried to save a user without an ID."


class NoPermissionsException(DigiException):
    level = logging.ERROR

    def formatMessage(self):
        return "SizeBot does not have the permssions to perform this action."


class InvalidUnitSystemException(DigiException):
    def __init__(self, unitsystem):
        self.unitsystem = unitsystem

    def formatUserMessage(self):
        return f"{self.unitsystem!r} is an unrecognized unit system."


class InvalidSizeValue(DigiException):
    def __init__(self, sizevalue):
        self.sizevalue = sizevalue

    def formatUserMessage(self):
        return f"{self.sizevalue!r} is an unrecognized size value."


class InvalidObject(DigiException):
    def __init__(self, name):
        self.name = name

    def formatUserMessage(self):
        return f"{self.name!r} is an unrecognized object."


class InvalidMacrovisionModelException(DigiException):
    def __init__(self, name):
        self.name = name

    def formatMessage(self):
        return f"{self.name!r} is an unrecognized Macrovision model."

    def formatUserMessage(self):
        return f"{self.name!r} is an unrecognized Macrovision model."


class InvalidMacrovisionViewException(DigiException):
    def __init__(self, model, view):
        self.model = model
        self.view = view

        if self.model not in modelJSON.keys():
            raise InvalidMacrovisionModelException(self.model)

    def formatMessage(self):
        return f"{self.view!r} is an unrecognized view for the Macrovision model {self.model!r}."

    def formatUserMessage(self):
        return f"{self.view!r} is an unrecognized view for the Macrovision model {self.model!r}."


class InvalidRollException(DigiException):
    def __init__(self, dString):
        self.dString = dString

    def formatUserMessage(self):
        return f"Invalid roll string `{self.dString}`."


class AdminPermissionException(DigiContextException):
    async def formatMessage(self, ctx):
        usernick = ctx.author.display_name
        return f"{usernick} tried to run an admin command."

    async def formatUserMessage(self, ctx):
        usernick = ctx.author.display_name
        return f"{usernick} tried to run an admin command. This incident will be reported."


class MultilineAsNonFirstCommandException(DigiContextException):
    async def formatMessage(self, ctx):
        usernick = ctx.author.display_name
        return f"{usernick} tried to run a multi-line command in the middle of a sequence."

    async def formatUserMessage(self, ctx):
        return "You are unable to run a command that takes a multi-line argument in the middle of a batch command sequence. Please try running these commands seperately."


class ArgumentException(DigiContextException):
    async def formatUserMessage(self, ctx):
        return f"Please enter `{ctx.prefix}{ctx.invoked_with} {ctx.command.signature}`."


class UserMessedUpException(DigiContextException):
    def __init__(self, custommessage):
        self.custommessage = custommessage

    async def formatUserMessage(self, ctx):
        return self.custommessage


class ThisShouldNeverHappenException(DigiException):
    level = logging.CRITICAL

    def formatMessage(self):
        return "This should never happen. Something very wrong has occured."


class ParseError(DigiException):
    def formatMessage(self, s, t):
        return f"Could not parse {s} into a {t}."
