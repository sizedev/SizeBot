import discord
from discord.ext import commands
from globalsb import *
import digilogger as logger

#Commands for non-size stuff.
#
#Commands:

class FunCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def repeat(self, ctx, delay : float, *, message : str):
		await ctx.message.delete()
		async def repeattask():
			while True:
				await ctx.send(message)
				await asyncio.sleep(delay * 60)
		task = bot.loop.create_task(repeattask())
		tasks[ctx.message.author.id] = task

	@commands.command()
	async def stoprepeat(self, ctx):
		await ctx.message.delete()
		tasks[ctx.message.author.id].cancel()
		del tasks[ctx.message.author.id]

	@commands.command()
	async def say(self, ctx, *, message : str):
		await ctx.message.delete()
		if ctx.message.author.id == digiid:
			await ctx.send(message)

	@commands.command()
	async def sing(self, ctx, *, string : str):
		await ctx.message.delete()
		newstring = ":musical_score: *" + string + "* :musical_note:"
		await ctx.send(newstring)

	@commands.command()
	async def winkcount(self, ctx):
		winkfile = open("../winkcount.txt", "r")
		winkcount = int(winkfile.read())
		await ctx.send(f"Yukio has winked {winkcount} times! :wink:")
		logger.msg(f"Wink count requested: {winkcount} times!")
		winkfile.close()

#Necessary.
def setup(bot):
	bot.add_cog(FunCog(bot))
