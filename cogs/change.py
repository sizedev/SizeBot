import discord
from discord.ext import commands
from globalsb import *

class ChangeCog:
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def change(self, ctx, style, amount):
		#Change height.
		if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
		#User file missing.
			await ctx.send("""Sorry! You aren't registered with SizeBot.
	To register, use the `&register` command.""", delete_after=5)
		elif style == "a" or style == "+" or style == "add":
			amount = isFeetAndInchesAndIfSoFixIt(amount)
			userarray = read_user(ctx.message.author.id)
			userarray[CHEI] = str(Decimal(userarray[CHEI]) + Decimal(toSV(getnum(amount), getlet(amount)))) + newline
			if (float(userarray[CHEI]) > infinity):
				print(warn("Invalid size value."))
				await ctx.send("Too big. x_x", delete_after=3)
				userarray[CHEI] = str(infinity) + newline
			write_user(ctx.message.author.id, userarray)
			userarray = read_user(ctx.message.author.id)
			print (userarray)
			if userarray[DISP] == "Y\n":
				await nickupdate(ctx, userarray)
			await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI]))) #Add comp to base.
		elif style == "m" or style == "*" or style == "x" or style == "mult" or style == "multiply":
			userarray = read_user(ctx.message.author.id)
			userarray[CHEI] = str(Decimal(userarray[CHEI]) * Decimal(amount)) + newline
			if (float(userarray[CHEI]) > infinity):
				print(warn("Invalid size value."))
				await ctx.send("Too big. x_x", delete_after=3)
				userarray[CHEI] = str(infinity) + newline
			write_user(ctx.message.author.id, userarray)
			userarray = read_user(ctx.message.author.id)
			print (userarray)
			if userarray[DISP] == "Y\n":
				await nickupdate(ctx, userarray)
				await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
		elif style == "s" or style == "-" or style == "sub" or style == "subtract":
			amount = isFeetAndInchesAndIfSoFixIt(amount)
			userarray = read_user(ctx.message.author.id)
			userarray[CHEI] = str(Decimal(userarray[CHEI]) - (toSV(getnum(amount), getlet(amount))))
			if (float(userarray[CHEI]) > infinity):
				print(warn("Invalid size value."))
				await ctx.send("Too big. x_x", delete_after=3)
				userarray[CHEI] = str(infinity) + newline
			write_user(ctx.message.author.id, userarray)
			userarray = read_user(ctx.message.author.id)
			print (userarray)
			if userarray[DISP] == "Y\n":
				await nickupdate(ctx, userarray)
				await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
		elif style == "d" or style == "/" or style == "div" or style == "divide":
			userarray = read_user(ctx.message.author.id)
			userarray[CHEI] = str(Decimal(userarray[CHEI]) / Decimal(amount))
			if (float(userarray[CHEI]) > infinity):
				print(warn("Invalid size value."))
				await ctx.send("Too big. x_x", delete_after=3)
				userarray[CHEI] = str(infinity) + newline
			write_user(ctx.message.author.id, userarray)
			userarray = read_user(ctx.message.author.id)
			print (userarray)
			if userarray[DISP] == "Y\n":
				await nickupdate(ctx, userarray)
				await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
		else:
			await ctx.send("Please enter a valid change method.", delete_after=3)
			return

	@commands.command()
	async def slowchange(self, ctx, style : str, amount : str, delay : float):
		async def slowchangetask():
			#Change height.
			if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
			#User file missing.
				await ctx.send("""Sorry! You aren't registered with SizeBot.
		To register, use the `&register` command.""", delete_after=5)
			elif style == "a" or style == "+" or style == "add":
				while True:
					amount = isFeetAndInchesAndIfSoFixIt(amount)
					userarray = read_user(ctx.message.author.id)
					userarray[CHEI] = str(Decimal(userarray[CHEI]) + Decimal(toSV(getnum(amount), getlet(amount)))) + newline
					if (float(userarray[CHEI]) > infinity):
						print(warn("Invalid size value."))
						await ctx.send("Too big. x_x", delete_after=3)
						userarray[CHEI] = str(infinity) + newline
						tasks[ctx.message.author.id].cancel()
						del tasks[ctx.message.author.id]
					write_user(ctx.message.author.id, userarray)
					userarray = read_user(ctx.message.author.id)
					print (userarray)
					if userarray[DISP] == "Y\n":
						await nickupdate(ctx, userarray)
					await ctx.send("""<@{0}> is now {1} tall. ({2})""".format(ctx.message.author.id, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
					await asyncio.sleep(delay * 60)
			elif style == "m" or style == "*" or style == "x" or style == "mult" or style == "multiply":
				while True:
					userarray = read_user(ctx.message.author.id)
					userarray[CHEI] = str(Decimal(userarray[CHEI]) * Decimal(amount)) + newline
					if (float(userarray[CHEI]) > infinity):
						print(warn("Invalid size value."))
						await ctx.send("Too big. x_x", delete_after=3)
						uuserarray[CHEI] = str(infinity) + newline
						tasks[ctx.message.author.id].cancel()
						del tasks[ctx.message.author.id]
					write_user(ctx.message.author.id, userarray)
					userarray = read_user(ctx.message.author.id)
					print (userarray)
					if userarray[DISP] == "Y\n":
						await nickupdate(ctx, userarray)
						await ctx.send("""{0} is now {1} tall. ({2})""".format(ctx.message.author.name, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
						await asyncio.sleep(delay * 60)
			elif style == "s" or style == "-" or style == "sub" or style == "subtract":
				while True:
					amount = isFeetAndInchesAndIfSoFixIt(amount)
					userarray = read_user(ctx.message.author.id)
					userarray[CHEI] = str(Decimal(userarray[CHEI]) - (toSV(getnum(amount), getlet(amount))))
					write_user(ctx.message.author.id, userarray)
					userarray = read_user(ctx.message.author.id)
					print (userarray)
					if userarray[DISP] == "Y\n":
						await nickupdate(ctx, userarray)
						await ctx.send("""{0} is now {1} tall. ({2})""".format(ctx.message.author.name, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
						await asyncio.sleep(delay * 60)
			elif style == "d" or style == "/" or style == "div" or style == "divide":
				while True:
					userarray = read_user(ctx.message.author.id)
					userarray[CHEI] = str(Decimal(userarray[CHEI]) / Decimal(amount))
					write_user(ctx.message.author.id, userarray)
					userarray = read_user(ctx.message.author.id)
					print (userarray)
					if userarray[DISP] == "Y\n":
						await nickupdate(ctx, userarray)
						await ctx.send("""{0} is now {1} tall. ({2})""".format(ctx.message.author.name, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])), delete_after = 5) #Add comp to base.
						await asyncio.sleep(delay * 60)
			else:
				await ctx.send("Please enter a valid change style.", delete_after=3)
		bot = self.bot
		task = bot.loop.create_task(slowchangetask())
		tasks[ctx.message.author.id] = task

	@commands.command()
	async def stopchange(self, ctx):
		tasks[ctx.message.author.id].cancel()
		del tasks[ctx.message.author.id]

	@commands.command()
	async def eatme(self, ctx):
		#Eat me!
		if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
		#User file missing.
			await ctx.send("""Sorry! You aren't registered with SizeBot.
	To register, use the `&register` command.""", delete_after=5)
		else:
			userarray = read_user(ctx.message.author.id)
			randmult = random.randint(2, 20)
			newheight = float(userarray[CHEI]) * randmult
			userarray[CHEI] = str(newheight) + newline
			if (float(userarray[CHEI]) > infinity):
				print(warn("Invalid size value."))
				await ctx.send("Too big. x_x", delete_after=3)
				userarray[CHEI] = str(infinity) + newline
			write_user(ctx.message.author.id, userarray)
			userarray = read_user(ctx.message.author.id)
			print (userarray)
			if userarray[DISP] == "Y\n":
				await nickupdate(ctx, userarray)
			#TODO: Randomize the italics message here.
			await ctx.send("""<@{0}> ate a :cake:! *I mean it said "Eat me..."*
They multiplied {1}x and are now {2} tall. ({3})""".format(ctx.message.author.id, randmult, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))

	@commands.command()
	async def drinkme(self, ctx):
		#Drink me!
		if not os.path.exists(folder + '/users/' + str(ctx.message.author.id) + '.txt'):
		#User file missing.
			await ctx.send("""Sorry! You aren't registered with SizeBot.
	To register, use the `&register` command.""", delete_after=5)
		else:
			userarray = read_user(ctx.message.author.id)
			randmult = random.randint(2, 20)
			newheight = float(userarray[CHEI]) / randmult
			userarray[CHEI] = str(newheight) + newline
			if (float(userarray[CHEI]) > infinity):
				print(warn("Invalid size value."))
				await ctx.send("Too big. x_x", delete_after=3)
				userarray[CHEI] = str(infinity) + newline
			write_user(ctx.message.author.id, userarray)
			userarray = read_user(ctx.message.author.id)
			print (userarray)
			if userarray[DISP] == "Y\n":
				await nickupdate(ctx, userarray)
			#TODO: Randomize the italics message here.
			await ctx.send("""<@{0}> drank a :milk:! *What harm could a drink do?*
They shrunk {1}x and are now {2} tall. ({3})""".format(ctx.message.author.id, randmult, fromSV(userarray[CHEI]), fromSVUSA(userarray[CHEI])))



#Necessary.
def setup(bot):
	bot.add_cog(ChangeCog(bot))
