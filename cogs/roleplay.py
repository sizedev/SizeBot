import discord
from discord.ext import commands
from globalsb import *

#Commands for roleplaying.
#
#Commands: roll

class RPCog:
	def __init__(self, bot):
		self.bot = bot

	#Die rolling command. XdY format.
	@commands.command()
	async def roll(self, ctx, dice):
		await ctx.message.delete()
		#Check to make sure the user used XdY notation.
		try:
			rolls, limit = map(int, dice.split('d'))
		except Exception:
			await ctx.send('Format has to be in XdY.')
			return
		if rolls > 100:
		#Don't let them roll a ton of dice.
			await ctx.send('Too many dice! Try again.')
			print(warn("User {0} tried to roll {1} dice.".format(ctx.message.author.name, rolls)))
			return
		if limit > 1000:
		#Keep number of sides rational.
			await ctx.send('Dice too big! Try again.')
			print(warn("User {0} tried to roll a {1}-sided dice.".format(ctx.message.author.name, limit)))
			return

		#Prettify the individual roll list.
		result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
		resultarray = result.split(", ")

		#Tabulate total.
		total = 0
		for x in resultarray:
			total = total + int(x)

		#Output the results to chat.
		await ctx.send('''<@{0}> rolled {1}!
			Result(s): {2}
			Total: {3}'''.format(ctx.message.author.id, dice, result, total))

#Necessary.
def setup(bot):
	bot.add_cog(RPCog(bot))
