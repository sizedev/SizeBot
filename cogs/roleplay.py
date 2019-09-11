import discord
from discord.ext import commands
from globalsb import *

#Commands for roleplaying.
#
#Commands: roll

class RPCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	#Die rolling command. XdY format.
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
			await ctx.send('Format has to be in XdY or XdYdZ.')
			return
		if dSides > 1000000:
			await ctx.send('Too many sides!')
			warn(f"{ctx.message.user.id} ({ctx.message.user.nick}) tried to roll a {dSides}-sided die!")
			stop = True
		if dNum > 250:
			await ctx.send('Too many dice!')
			warn(f"{ctx.message.user.id} ({ctx.message.user.nick}) tried to roll {dNum} dice!")
			stop = True
		if stop: return
		for x in range(dNum):
			currentRoll = (random.randrange(1, dSides + 1))
			rolls.append(currentRoll)
		rolls.sort(key=int)
		for x in range(dDrops, len(rolls)):
			dTotal = dTotal + rolls[x]
			usedrolls.append(rolls[x])
		dropped = rolls
		for item in usedrolls: dropped.remove(item)
		sendstring = "{0} rolled {1} and got {2}!\nDice: {3}".format(ctx.message.author.nick, dString, str(dTotal), str(usedrolls))
		if dropped != []: sendstring = sendstring + "\n~~Dropped: {0}~~".format(str(dropped))
		(f"{ctx.message.user.id} ({ctx.message.user.nick}) rolled {dString}.")
		await ctx.send(sendstring)

#Necessary.
def setup(bot):
	bot.add_cog(RPCog(bot))
