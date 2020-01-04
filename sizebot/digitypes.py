from discord.ext import commands
from sizebot.digiSV import toSV


class SV(commands.Converter):
    async def convert(self, ctx, argument):
        heightsv = toSV(argument)
        if heightsv is None:
            raise commands.errors.BadArgument
        return heightsv
