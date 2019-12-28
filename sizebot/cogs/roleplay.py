import random

from discord.ext import commands

from sizebot import digilogger as logger


# Commands for roleplaying.
#
# Commands: roll
class RPCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Die rolling command. XdY format.
    @commands.command()
    async def roll(self, ctx, dString):
        rolls = []
        usedrolls = []
        dSides = 0
        dNum = 0
        dDrops = 0
        dTotal = 0
        stop = False
        dArray = dString.split("d")
        if len(dArray) == 2:
            dNum = int(dArray[0])
            dSides = int(dArray[1])
        elif len(dArray) == 3:
            dNum = int(dArray[0])
            dSides = int(dArray[1])
            dDrops = int(dArray[2])
        else:
            await ctx.send("Format has to be in XdY or XdYdZ.")
            return
        if dSides > 1000000:
            await ctx.send("Too many sides!")
            await logger.warn(f"{ctx.message.author.id} ({ctx.message.author.display_name}) tried to roll a {dSides}-sided die!")
            stop = True
        if dNum > 250:
            await ctx.send("Too many dice!")
            await logger.warn(f"{ctx.message.author.id} ({ctx.message.author.display_name}) tried to roll {dNum} dice!")
            stop = True
        if stop:
            return
        for x in range(dNum):
            currentRoll = (random.randrange(1, dSides + 1))
            rolls.append(currentRoll)
        rolls.sort(key = int)
        for x in range(dDrops, len(rolls)):
            dTotal = dTotal + rolls[x]
            usedrolls.append(rolls[x])
        dropped = rolls
        for item in usedrolls:
            dropped.remove(item)
        sendstring = f"{ctx.message.author.display_name} rolled {dString} and got {dTotal}!\nDice: {usedrolls}"
        if dropped != []:
            sendstring = sendstring + f"\n~~Dropped: {dropped}~~"
        await logger.info(f"{ctx.message.author.id} ({ctx.message.author.display_name}) rolled {dString}.")
        await ctx.send(sendstring)


# Necessary
def setup(bot):
    bot.add_cog(RPCog(bot))
