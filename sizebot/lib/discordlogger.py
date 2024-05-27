import asyncio
import contextlib
import logging

import discord

from sizebot.lib.utils import chunk_msg


class AsyncHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.__queue: asyncio.Queue[logging.LogRecord] = asyncio.Queue()
        asyncio.create_task(self.__loop())
        super().__init__(*args, **kwargs)

    def emit(self, record: logging.LogRecord):
        self.__queue.put_nowait(record)

    def asyncemit(self, record: logging.LogRecord):
        raise NotImplementedError

    async def __loop(self):
        while True:
            record = await self.__queue.get()
            with contextlib.suppress(Exception):
                await self.asyncemit(record)


class DiscordHandler(AsyncHandler):
    def __init__(self, channel: discord.TextChannel):
        super().__init__()
        self.__channel = channel

    async def asyncemit(self, record: logging.LogRecord):
        message = record.getMessage().replace("```", r"\`\`\`")

        for m in chunk_msg(message):
            await self.__channel.send(m)
