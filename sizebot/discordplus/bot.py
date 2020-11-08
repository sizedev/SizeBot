from discord.ext.commands.bot import BotBase
import logging
from sizebot.lib import errors
# from copy import copy

logger = logging.getLogger("sizebot")

old_dispatch = BotBase.dispatch
first_ready = True


async def process_commands(self, message):
    if message.author.bot:
        return

    contexts = []

    ctx = await self.get_context(message)

    if ctx.command and ctx.command.multiline:  # Command string starts with a multiline command, assume it's all one command
        contexts.append(ctx)
    elif not ctx.command:  # No command found, invoke will handle it
        contexts.append(ctx)
    else:  # The first command is not multiline
        lines = message.content.split("\n")
        for line in lines:
            message.content = line
            newctx = await self.get_context(message)
            contexts.append(newctx)

    for context in contexts:
        if context.command and context.command.multiline and len(contexts) != 1:  # This should only happen if they're the second arugment since we caught that earlier
            await context.command.dispatch_error(context, errors.MultilineAsNonFirstCommandException(context))
            return

    for context in contexts:
        await self.invoke(context)


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
    BotBase.process_commands = process_commands
