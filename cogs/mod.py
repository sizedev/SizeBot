import discord
from discord.ext import commands
from globalsb import *

class ModCog:
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def heightunits(self, ctx):
		await ctx.message.delete()
		await ctx.send("""<@{0}>, **Accepted Units**
	*Height*
	```
	┌─────────────────────────┬───────────────────────────┐
	│       Metric            │         Imperial          │
	├─────────────────────────┼───────────────────────────┤
	│ ym (yoctometer[s])      │ in (inch[es])             │
	│ zm (zeptometer[s])      │ ft (feet)                 │
	│ am (attometer[s])       │ mi (mile[s])              │
	│ fm (femtometer[s])      │ AU (astronomical_unit[s]) │
	│ pm (picometer[s])       │ uni (universe[s])         │
	│ nm (nanometer[s])       │                           │
	│ µm (micrometer[s])      │                           │
	│ mm (millimeter[s])      │                           │
	│ cm (centimeter[s])      │                           │
	│ m (meter[s])            │                           │
	│ km (kilometer[s])       │                           │
	│ Mm (megameter[s])       │                           │
	│ Gm (gigameter[s])       │                           │
	│ Tm (terameter[s])       │                           │
	│ Pm (petameter[s])       │                           │
	│ Em (exameter[s])        │                           │
	│ Zm (zettameter[s])      │                           │
	│ Ym (yottameter[s])      │                           │
	│ uni (universe[s])       │                           │
	│ kuni (kilouniverse[s])  │                           │
	│ Muni (megauniverse[s])  │                           │
	│ Guni (gigauniverse[s])  │                           │
	│ Tuni (terauniverse[s])  │                           │
	│ Puni (petauniverse[s])  │                           │
	│ Euni (exauniverse[s])   │                           │
	│ Zuni (zettauniverse[s]) │                           │
	│ Yuni (yottauniverse[s]) │                           │
	└─────────────────────────┴───────────────────────────┘```""".format(ctx.message.author.id))

	@commands.command()
	async def weightunits(self, ctx):
		await ctx.message.delete()
		await ctx.send("""<@{0}>, **Accepted Units**
	*Weight*
	```
	┌─────────────────────────┬───────────────────────────┐
	│       Metric            │         Imperial          │
	├─────────────────────────┼───────────────────────────┤
	│ yg (yoctogram[s])       │ oz (ounce[s])             │
	│ zg (zeptogram[s])       │ lbs (pound[s])            │
	│ ag (attogram[s])        │ Earth[s]                  │
	│ fg (femtogram[s])       │ Sun[s]                    │
	│ pg (picogram[s])        │                           │
	│ ng (nanogram[s])        │                           │
	│ µg (microgram[s])       │                           │
	│ mg (milligram[s])       │                           │
	│ g (gram[s])             │                           │
	│ kg (kilogram[s])        │                           │
	│ t (ton[s])              │                           │
	│ kt (kiloton[s])         │                           │
	│ Mt (megaton[s])         │                           │
	│ Gt (gigaton[s])         │                           │
	│ Tt (teraton[s])         │                           │
	│ Pt (petaton[s])         │                           │
	│ Et (exaton[s])          │                           │
	│ Zt (zettaton[s])        │                           │
	│ Yt (yottaton[s])        │                           │
	│ uni (universe[s])       │                           │
	│ kuni (kilouniverse[s])  │                           │
	│ Muni (megauniverse[s])  │                           │
	│ Guni (gigauniverse[s])  │                           │
	│ Tuni (terauniverse[s])  │                           │
	│ Puni (petauniverse[s])  │                           │
	│ Euni (exauniverse[s])   │                           │
	│ Zuni (zettauniverse[s]) │                           │
	│ Yuni (yottauniverse[s]) │                           │
	└─────────────────────────┴───────────────────────────┘```""".format(ctx.message.author.id))

	@commands.command()
	async def help(self, ctx, what:str = None):
		await ctx.message.delete()
		if what is None:
			await ctx.send("""<@{0}>, **Help Topics**
	***☞*** *`[]` indicates a required parameter, `<>` indicates an optional parameter.*

	*Commands*
	```
	register "[nickname]" [Y/N]† [current height] [base height] [base weight] [U/M]†† "<species>"```
	*† Indicates whether you want SizeBot to automatically set and continue to manage your nickname and sizetag.*
	*†† Indicates which system to use for your sizetag. U = US, M = metric.*
	```
	unregister
	stats <user>
	change [x,/,+,-] [value]
	setheight [height]
	set0
	setinf
	setbaseheight [height]
	setbaseweight [weight]
	setrandomheight [minheight] [maxheight]
	slowchange [x,/,+,-] [amount] [delay]
	stopchange
	roll XdY
	changenick [nick]
	setspecies [species]
	clearspecies
	setdisplay [Y/N]
	compare [user1] <user2>
	statsraw [size]
	compareraw [size]
	sing [string]```

	*Other Topics*
	```
	heightunits
	weightunits
	about
	donate
	bug```""".format(ctx.message.author.id))

	@commands.command()
	async def about(self, ctx):
		await ctx.message.delete()
		await ctx.send("```\n" + ascii + "```")
		await ctx.send("""<@{0}>
	***SizeBot3 by DigiDuncan***
	*A big program for big people.*
	**Written for the Size Haven server and adapted for Size Matters**
	**Slogan** **by Twitchy**
	**Additional equations** *by Benyovski and Arceus3251*
	**Coding Assistance** *by Natalie*
	**Alpha Tested** *by AWK_*
	**Beta Tested** *by Speedbird 001, worstgender, Arceus3251*
	**written in** *Python 3.7 with discord.py rewrite*
	**written with** Atom
	**Special thanks** *to Reol, jyubari, and Memekip for making the Size Matters server*
	**Special thanks** *to the discord.py Community Discord for helping with code*
	**Special thanks** to the {1} users of SizeBot3.

	"She (*SizeBot*) is beautiful." -- *GoddessArete*
	":100::thumbsup:" -- *Anonymous*
	"I am the only person who has accidentally turned my fetish into a tech support job." -- *DigiDuncan*

	Version {2} | 15 Jun 2019""".format(ctx.message.author.id, members, version))

	@commands.command()
	async def donate(self, ctx):
		await ctx.message.delete()
		await ctx.send("""<@{0}>
SizeBot is coded (mainly) by DigiDuncan, and for absolutely free.
However, if you wish to contribute to DigiDuncan directly, you can do so here:
https://paypal.me/DigiDuncanPayPal
SizeBot has been a passion project coded over a period of two years and learning a lot of Python along the way.
Thank you so much for being here throughout this journey!""".format(ctx.message.author.id))

	@commands.command()
	async def bug(self, ctx, *, message : str):
		await bot.get_user(digiid).send("<@{0}>: {1}".format(ctx.message.author.id, message))

#Necessary.
def setup(bot):
	bot.add_cog(ModCog(bot))
