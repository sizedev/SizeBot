import asyncio
import logging

from sizebot.lib.utils import chunkMsg


class AsyncHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.__queue = asyncio.Queue()
        asyncio.create_task(self.__loop())
        super().__init__(*args, **kwargs)

    def emit(self, record):
        self.__queue.put_nowait(record)

    def asyncemit(self, record):
        raise NotImplementedError

    async def __loop(self):
        while True:
            record = await self.__queue.get()
            try:
                await self.asyncemit(record)
            except Exception:
                pass


class DiscordHandler(AsyncHandler):
    def __init__(self, channel):
        super().__init__()
        self.__channel = channel

    async def asyncemit(self, record):
        message = record.getMessage().replace("```", r"\`\`\`")

        for m in chunkMsg(message):
            await self.__channel.send(m)
