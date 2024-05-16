from __future__ import annotations
from typing import cast

import asyncio

from discord.ext import commands
from discord import Embed, Emoji, PartialEmoji, Reaction, Member, User, Message

from sizebot.lib.errors import DigiException


class TooManyMenuOptionsException(DigiException):
    # TODO: CamelCase
    def formatMessage(self):
        return "Too many options for this reaction menu. (limit is 20.)"


EmojiInputType = Emoji | PartialEmoji | str


class Menu:
    """Creates a reaction-based menu in a Discord message.

    Required Arguments:
    ctx: A Discord context (discord.ext.commands.context.Context).
    options: a list of either valid Unicode emojis or Discord Emoji objects. (up to 20, or 19 if `cancel_emoji`.)

    Keyword Arguments:
    initial_message: what you want the menu to message to say first. Default = "".
    timeout: when to stop accepting reactions (a seconds value as a float). Default = 60.0
    delete: whether to delete the message when the menu is done accepting options. Default = True
    cancel_emoji: either a valid Unicode emoji or Discord Emoji object to exit the menu. Default = None

    Properties:
    menu_owner: the Member object that asked for this menu.
    """

    def __init__(self, ctx: commands.Context, options: list[EmojiInputType], *,
                 initial_message: str | None = None, initial_embed: Embed | None = None, timeout: float = 60,
                 delete_after: bool = True, allow_any: bool = False, cancel_emoji: EmojiInputType | None):
        self.ctx = ctx
        self.initial_message = initial_message
        self.initial_embed = initial_embed
        self.options = options
        self.timeout = timeout
        self.delete_after = delete_after
        self.allow_any = allow_any
        self.cancel_emoji = cancel_emoji

        if len(self.options) + int(bool(self.cancel_emoji)) > 20:
            raise TooManyMenuOptionsException

    @property
    def menu_owner(self) -> User | Member:
        return self.ctx.author

    def __str__(self):
        return f"{self.ctx=} | {self.initial_message=} | {self.options=} | {self.timeout=} | {self.delete_after=} | {self.allow_any=} | {self.cancel_emoji=}"

    async def run(self) -> EmojiInputType | None:
        message = cast(Message, await self.ctx.send(self.initial_message, embed = self.initial_embed))

        # Add all the reactions we need.
        for option in self.options:
            await message.add_reaction(option)
        if self.cancel_emoji:
            await message.add_reaction(self.cancel_emoji)

        # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
        def check(reaction: Reaction, reacter: Member | User) -> bool:
            return reaction.message.id == message.id \
                and (self.allow_any or reacter.id == self.menu_owner.id) \
                and (
                    str(reaction.emoji) == self.cancel_emoji
                    or str(reaction.emoji) in self.options
                )

        # Wait for a reaction.
        reaction = None
        try:
            reaction, reacter = cast(tuple[Reaction, Member | User], await self.ctx.bot.wait_for("reaction_add", timeout=self.timeout, check=check))
        except asyncio.TimeoutError:
            # User took too long to respond
            pass

        if self.delete_after:
            await message.delete()
            message = None

        if reaction is None or reaction.emoji == self.cancel_emoji:
            # User took too long to respond
            # or the reaction is cancel, stop.
            answer = None
        else:
            # If the reaction is the right one, return what it is.
            answer = reaction.emoji

        # Let's wrap things up.
        if message:
            # PERMISSION: requires manage_messages
            await message.clear_reactions()
        return answer

    @classmethod
    async def display(cls, *args, **kwargs) -> tuple[Menu, EmojiInputType | None]:
        reactionmenu = Menu(*args, **kwargs)
        answer = await reactionmenu.run()
        return reactionmenu, answer

# class LoopingMenu:
#     """Creates a reaction-based menu in a Discord message that can accept multiple inputs.

#     Required Arguments:
#     ctx: A Discord context (discord.ext.commands.context.Context).
#     options: a list of either valid Unicode emojis or Discord Emoji objects. (up to 20, or 19 if `cancel_emoji`.)

#     Keyword Arguments:
#     success_function: A function to run after a correct option is chosen.
#     timeout: when to stop accepting reactions (a seconds value as a float). Default = 60.0
#     delete: whether to delete the message when the menu is done accepting options. Default = True
#     remove_reaction: Whether to remove the reaction after it's added, allows the same user to choose
#     the same option multiple times. Default = True
#     cancel_emoji: either a valid Unicode emoji or Discord Emoji object to exit the menu. Default = None
#     """

#     def __init__(self, ctx: commands.context.Context, options: list, success_function = None, *,
#                  timeout: float = 60, delete: bool = True, allow_any: bool = False, remove_reaction = True, cancel_emoji: None):
#         self.ctx = ctx
#         self.options = options
#         self.success_function = success_function
#         self.timeout = timeout
#         self.delete = delete
#         self.allow_any = allow_any
#         self.cancel_emoji = cancel_emoji

#         if len(self.options) + int(self.cancel_emoji) > 20:
#             raise TooManyMenuOptionsException

#     def run(self):
#         pass
