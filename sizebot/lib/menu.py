import asyncio

from discord.ext import commands

from sizebot.lib.errors import DigiException


class TooManyMenuOptionsException(DigiException):
    def formatMessage(self):
        return "Too many options for this reaction menu. (limit is 20.)"


class Menu:
    """Creates a reaction-based menu in a Discord message.

    Required Arguments:
    ctx: A Discord context (discord.ext.commands.context.Context).
    options: a list of either valid Unicode emojis or Discord Emoji objects. (up to 20, or 19 if `cancel_emoji`.)

    Keyword Arguments:
    timeout: when to stop accepting reactions (a seconds value as a float). Default = 60.0
    delete: whether to delete the message when the menu is done accepting options. Default = True
    cancel_emoji: either a valid Unicode emoji or Discord Emoji object to exit the menu. Default = None
    """

    def __init__(self, ctx: commands.context.Context, options: list, *,
                 timeout: float = 60, delete: bool = True, only_sender: bool = True, cancel_emoji: None):
        self.ctx = ctx
        self.options = options
        self.timeout = timeout
        self.delete = delete
        self.only_sender = only_sender
        self.cancel_emoji = cancel_emoji

        if len(self.options) + int(bool(self.cancel_emoji)) > 20:
            raise TooManyMenuOptionsException

    def debug(self):
        return f"{self.ctx=} | {self.options=} | {self.timeout=} | {self.delete=} | {self.only_sender=} {self.cancel_emoji=}"

    async def run(self):

        # Add all the reactions we need.
        for option in self.options:
            await self.ctx.message.add_reaction(option)
        if self.cancel_emoji:
            await self.ctx.message.add_reaction(self.cancel_emoji)

        # Wait for requesting user to react to sent message with emojis.check or emojis.cancel
        def check(reaction, reacter):
            correctreactor = not self.only_sender or reacter.id == self.ctx.message.author.id
            return reaction.message.id == self.ctx.message.id \
                and correctreactor \
                and (
                    str(reaction.emoji) == self.cancel_emoji
                    or str(reaction.emoji) in self.options
                )

        # Wait for a reaction.
        try:
            reaction, self.ctx.message.author = await self.ctx.bot.wait_for("reaction_add", timeout=self.timeout, check=check)
        except asyncio.TimeoutError:
            # User took too long to respond
            if self.delete:
                await self.ctx.message.delete()
            return

        # If the reaction is cancel, stop.
        if self.cancel_emoji:
            if reaction.emoji == self.cancel_emoji:
                if self.delete:
                    await self.ctx.message.delete()
                    return

        # If the reaction is the right one, return what it is.
        if reaction.emoji in self.options:
            if self.delete():
                self.ctx.message.delete()
            return reaction.emoji


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
#                  timeout: float = 60, delete: bool = True, only_sender: bool = True, remove_reaction = True, cancel_emoji: None):
#         self.ctx = ctx
#         self.options = options
#         self.success_function = success_function
#         self.timeout = timeout
#         self.delete = delete
#         self.only_sender = only_sender
#         self.cancel_emoji = cancel_emoji

#         if len(self.options) + int(self.cancel_emoji) > 20:
#             raise TooManyMenuOptionsException

#     def run(self):
#         pass
