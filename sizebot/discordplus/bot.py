from copy import copy

from discord.ext.commands.bot import BotBase
from discord.ext import commands

old_dispatch = BotBase.dispatch
first_ready = True


class BadMultilineCommand(commands.errors.CommandError):
    """A multiline command is being run in the middle of a list of commands"""
    pass


def find_one(iterable):
    try:
        return next(iterable)
    except StopIteration:
        return None


async def process_commands(self, message):
    if message.author.bot:
        return

    contexts = []

    ctx = await self.get_context(message)

    # No command found, invoke will handle it
    if not ctx.command:
        await self.invoke(ctx)
        return

    # One multiline command (command string starts with a multiline command)
    if ctx.command.multiline:
        await self.invoke(ctx)
        return

    # Multiple commands (first command is not multiline)
    lines = message.content.split("\n")
    messages = []
    for line in lines:
        msg = copy(message)
        msg.content = line
        messages.append(msg)
    contexts = [await self.get_context(msg) for msg in messages]

    # If at least one of the lines does not start with a prefix, then ignore all the lines
    not_command = find_one(ctx for ctx in contexts if ctx.invoked_with is None)
    if not_command:
        return

    # If at least one of the lines don't match to a command, then throw an error for that command
    bad_command = find_one(ctx for ctx in contexts if ctx.command is None)
    if bad_command:
        await self.invoke(bad_command)
        return

    # If at least one of the lines is a multi-line command (these are only allowed as the first command)
    multiline_command = find_one(ctx for ctx in contexts if ctx.command.multiline)
    if multiline_command:
        username = multiline_command.author.display_name
        await multiline_command.command.dispatch_error(multiline_command, commands.errors.BadMultilineCommand(f"{username} tried to run a multi-line command in the middle of a sequence."))
        return

    # If all the lines have a command, then run them in order
    for ctx in contexts:
        await self.invoke(ctx)


def dispatch(self, event_name, *args, **kwargs):
    global first_ready
    old_dispatch(self, event_name, *args, **kwargs)
    if event_name == "ready":
        if first_ready:
            event_name = "first_ready"
            first_ready = False
        else:
            event_name = "reconnect_ready"
        old_dispatch(self, event_name, *args, **kwargs)


def patch():
    commands.errors.BadMultilineCommand = BadMultilineCommand
    commands.BadMultilineCommand = BadMultilineCommand
    BotBase.process_commands = process_commands
    BotBase.dispatch = dispatch
