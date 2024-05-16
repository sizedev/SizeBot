from typing import Any

import importlib.resources as pkg_resources
import logging
import json

from discord.ext import commands

import sizebot.data
from sizebot.conf import conf
from sizebot.lib import utils

modelJSON = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))


# error.message will be printed when you do print(error)
# error.user_message will be displayed to the user
class DigiException(Exception):
    level = logging.WARNING

    # TODO: CamelCase
    def formatMessage(self) -> str:
        return None

    # TODO: CamelCase
    def formatUserMessage(self) -> str:
        return None

    def __repr__(self):
        return utils.get_fullname(self)

    def __str__(self):
        return self.formatMessage() or self.formatUserMessage() or repr(self)


class DigiContextException(Exception):
    level = logging.WARNING

    # TODO: CamelCase
    async def formatMessage(self, ctx: commands.Context) -> str:
        return None

    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context) -> str:
        return None

    def __repr__(self):
        return utils.get_fullname(self)

    def __str__(self):
        return repr(self)


class UserNotFoundException(DigiContextException):
    def __init__(self, guildid: int, userid: int, unreg: bool = False):
        self.guildid = guildid
        self.userid = userid
        self.unreg = unreg

    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context):
        user = await ctx.guild.fetch_member(self.userid)
        usernick = user.display_name
        returnstr = f"Sorry, {usernick} isn't registered with SizeBot."
        if ctx.message.author.id == self.userid and not self.unreg:
            returnstr += f"\nTo register, use the `{conf.prefix}register` command."
        elif ctx.message.author.id == self.userid and self.unreg:
            returnstr += f"\nTo complete registration, use the `{conf.prefix}register` command to see your next step."
        return returnstr


class GuildNotFoundException(DigiException):
    def __init__(self, guildid: int):
        self.guildid = guildid

    # TODO: CamelCase
    def formatMessage(self):
        return f"Guild {self.guildid} not found."


class ValueIsZeroException(DigiException):
    # TODO: CamelCase
    def formatMessage(self):
        return "Value zero received when unexpected."

    # TODO: CamelCase
    def formatUserMessage(self):
        return (
            "Nice try.\n"
            "You can't change by a value of zero.")


class ValueIsOneException(DigiException):
    # TODO: CamelCase
    def formatMessage(self):
        return "Value one received when unexpected."

    # TODO: CamelCase
    def formatUserMessage(self):
        return (
            "Nice try.\n"
            "You can't change by a value of one.\n"
            "The reason for this is that it doesn't do anything, "
            "and this is a waste of memory and processing power for SizeBot, "
            "especially if the task is a repeating one.")


class ChangeMethodInvalidException(DigiContextException):
    def __init__(self, changemethod: str):
        self.changemethod = changemethod

    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context):
        usernick = ctx.author.display_name
        return f"Sorry, {usernick}! {self.changemethod} is not a valid change method."


class CannotSaveWithoutIDException(DigiException):
    level = logging.CRITICAL

    # TODO: CamelCase
    def formatMessage(self):
        return "Tried to save a user without an ID."


class NoPermissionsException(DigiException):
    level = logging.ERROR

    # TODO: CamelCase
    def formatMessage(self):
        return "SizeBot does not have the permssions to perform this action."


class InvalidUnitSystemException(DigiException):
    def __init__(self, unitsystem: str):
        self.unitsystem = unitsystem

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.unitsystem!r} is an unrecognized unit system."


class InvalidSizeValue(DigiException):
    def __init__(self, sizevalue: str, kind: str):
        self.sizevalue = sizevalue
        self.kind = kind

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.sizevalue!r} is an unrecognized {self.kind} value."


class InvalidStat(DigiException):
    def __init__(self, value: str):
        self.value = value

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.value!r} is an unrecognized stat."


class InvalidStatTag(DigiException):
    def __init__(self, value: str):
        self.value = value

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.value!r} is an unrecognized stat tag."


class InvalidObject(DigiException):
    def __init__(self, name: str):
        self.name = name

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.name!r} is an unrecognized object."


class InvalidMacrovisionModelException(DigiException):
    def __init__(self, name: str):
        self.name = name

    # TODO: CamelCase
    def formatMessage(self):
        return f"{self.name!r} is an unrecognized Macrovision model."

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.name!r} is an unrecognized Macrovision model."


class InvalidMacrovisionViewException(DigiException):
    def __init__(self, model: str, view: str):
        self.model = model
        self.view = view

        if self.model not in modelJSON.keys():
            raise InvalidMacrovisionModelException(self.model)

    # TODO: CamelCase
    def formatMessage(self):
        return f"{self.view!r} is an unrecognized view for the Macrovision model {self.model!r}."

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"{self.view!r} is an unrecognized view for the Macrovision model {self.model!r}."


class InvalidRollException(DigiException):
    def __init__(self, dString: str):
        self.dString = dString

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"Invalid roll string `{self.dString}`."


class AdminPermissionException(DigiContextException):
    # TODO: CamelCase
    async def formatMessage(self, ctx: commands.Context):
        usernick = ctx.author.display_name
        return f"{usernick} tried to run an admin command."

    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context):
        usernick = ctx.author.display_name
        return f"{usernick} tried to run an admin command. This incident will be reported."


class MultilineAsNonFirstCommandException(DigiContextException):
    # TODO: CamelCase
    async def formatMessage(self, ctx: commands.Context):
        usernick = ctx.author.display_name
        return f"{usernick} tried to run a multi-line command in the middle of a sequence."

    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context):
        return "You are unable to run a command that takes a multi-line argument in the middle of a batch command sequence. Please try running these commands seperately."


class ArgumentException(DigiContextException):
    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context):
        return f"Please enter `{ctx.prefix}{ctx.invoked_with} {ctx.command.signature}`."


class UserMessedUpException(DigiContextException):
    def __init__(self, custommessage: str):
        self.custommessage = custommessage

    # TODO: CamelCase
    async def formatMessage(self, ctx: commands.Context):
        usernick = ctx.author.display_name
        return usernick + ": " + self.custommessage

    # TODO: CamelCase
    async def formatUserMessage(self, ctx: commands.Context):
        return self.custommessage


class ThisShouldNeverHappenException(DigiException):
    level = logging.CRITICAL

    def __init__(self, custommessage: str):
        self.custommessage = custommessage

    # TODO: CamelCase
    def formatUserMessage(self):
        return "This should never happen. Something very wrong has occured."

    # TODO: CamelCase
    def formatMessage(self):
        return self.custommessage


class ParseError(DigiException):
    def __init__(self, s: str, t: str):
        self.s = s
        self.t = t

    # TODO: CamelCase
    def formatMessage(self):
        return f"Could not parse {self.s} into a {self.t}."

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"Could not parse {self.s} into a {self.t}."


class UnfoundStatException(DigiException):
    def __init__(self, s: list[Any]):
        self.s = utils.sentence_join(getattr(t, "key", repr(t)) for t in s)

    # TODO: CamelCase
    def formatMessage(self):
        return f"Could not calculate the {self.s} stat(s)."

    # TODO: CamelCase
    def formatUserMessage(self):
        return f"Could not calculate the {self.s} stat(s)."
