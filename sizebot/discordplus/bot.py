from discord.ext.commands.bot import BotBase
import logging

logger = logging.getLogger("sizebot")


async def process_commands(self, message):
    if message.author.bot:
        return

    ctx = await self.get_context(message)
    await self.invoke(ctx)
    logger.info("Ooh ooh ah ah! Monkey patched!")


def patch():
    BotBase.process_commands = process_commands
