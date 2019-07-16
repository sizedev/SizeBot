import discord
from discord.ext import commands
from globalsb import *

class StatsCog(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def stats(self, ctx, who : discord.Member = None):
		#footfactor = Decimal(12800) / Decimal(70000)
		footfactor = Decimal(1) / Decimal(7)
		footwidthfactor = footfactor / Decimal(2.5)
		footthickfactor = Decimal(1) / Decimal(65)
		thumbfactor = Decimal(1) / Decimal(26)
		fingerprintfactor = Decimal(1) / Decimal(35080)
		if who is None:
			who = ctx.message.author
		whoid = str(who.id)
		if not os.path.exists(folder + '/users/' + whoid + '.txt'):
		#User file missing.
			await ctx.send("""Sorry! User isn't registered with SizeBot.
	To register, use the `&register` command.""", delete_after=5)
		else:
			userarray = read_user(whoid)
			readableheight = fromSVacc(userarray[CHEI])
			readablefootheight = fromSVacc(Decimal(userarray[CHEI]) * footfactor)
			readablefootUSAheight = fromSVUSA(Decimal(userarray[CHEI]) * footfactor)
			readablefootthick = fromSVacc(Decimal(userarray[CHEI]) * footthickfactor)
			readablefootUSAthick = fromSVUSA(Decimal(userarray[CHEI]) * footthickfactor)
			readableUSAheight = fromSVUSA(userarray[CHEI])
			userbaseh = fromSV(userarray[BHEI])
			userbasehusa = fromSVUSA(userarray[BHEI])
			userbasew = fromWV(userarray[BWEI])
			userbasewusa = fromWVUSA(userarray[BWEI])
			density = Decimal(userarray[DENS])
			multiplier = Decimal(userarray[CHEI]) / Decimal(userarray[BHEI])
			basemult = Decimal(userarray[CHEI]) / Decimal(defaultheight)
			multipliercubed = multiplier**3
			basemultcubed = basemult**3
			baseweight = Decimal(userarray[BWEI])
			weightmath = (baseweight*(multipliercubed))*density
			readableweight = fromWV(weightmath)
			readableUSAweight = fromWVUSA(weightmath)
			normalheight = fromSVacc(Decimal(defaultheight)/Decimal(basemult))
			normalUSAheight = fromSVUSA(Decimal(defaultheight)/Decimal(basemult))
			normalweight = fromWV(Decimal(defaultweight)/Decimal(basemultcubed))
			normalUSAweight = fromWVUSA(Decimal(defaultweight) / Decimal(basemultcubed))
			thumbsize = fromSVacc(Decimal(userarray[CHEI]) * thumbfactor)
			thumbsizeUSA = fromSVUSA(Decimal(userarray[CHEI]) * thumbfactor)
			footheight = Decimal(userarray[CHEI]) * footfactor
			footwidth = fromSV(Decimal(userarray[CHEI]) * footwidthfactor)
			footwidthUSA = fromSVUSA(Decimal(userarray[CHEI]) * footwidthfactor)
			footlengthinches = Decimal(userarray[CHEI]) * footfactor / inch
			footlengthinches = round(footlengthinches, 3)
			shoesize = toShoeSize(footlengthinches)
			fingerprintdepth = fromSVacc(Decimal(userarray[CHEI]) * fingerprintfactor)
			fingerprintdepthUSA = fromSVUSA(Decimal(userarray[CHEI]) * fingerprintfactor)
			hcms = place_value(round(multiplier, 3))
			hbms = place_value(round(basemult, 3))
			wcms = place_value(round(multipliercubed * density, 3))
			wbms = place_value(round(basemultcubed * density, 3))
			if multiplier > 999999999999999:
				hcms = '{:.2e}'.format(multiplier)
			if basemult > 999999999999999:
				hbms = '{:.2e}'.format(basemult)
			if multipliercubed > 999999999999999:
				wcms = '{:.2e}'.format(multipliercubed * density)
			if basemultcubed > 999999999999999:
				wbms = '{:.2e}'.format(basemultcubed * density)

			await ctx.send("""**<@{0}> Stats:**
	Current Height: {1} | {2} ({3}x character base, {4}x normal)
	Current Weight: {5} | {6} ({7}x charbase, {8}x norm)
	Current Density: {9}x
	Foot Length: {10} | {11} ({12})
	Foot Width: {13} | {14}
	Toe Height: {15} | {16}
	Thumb Size: {17} | {18}
	Fingerprint Depth: {27} | {28}
	Size of a Normal Man (Comparative) {19} | {20}
	Weight of a Normal Man (Comparative) {21} | {22}
	Character Bases: {23}, {24} | {25}, {26}""".format(whoid, readableheight, readableUSAheight,
		hcms, hbms, readableweight, readableUSAweight,
		wcms, wbms, density, readablefootheight, readablefootUSAheight, shoesize,
		footwidth, footwidthUSA, readablefootthick, readablefootUSAthick,
		thumbsize, thumbsizeUSA,
		normalheight, normalUSAheight, normalweight, normalUSAweight,
		userbaseh, userbasehusa, userbasew, userbasewusa,
		fingerprintdepth, fingerprintdepthUSA))
		print("Stats for {0} sent.".format(who))
		pass

	@commands.command()
	async def statsraw(self, ctx, who : str):
		footfactor = Decimal(10000) / Decimal(70000)
		footwidthfactor = footfactor / Decimal(2.5)
		footthickfactor = Decimal(1) / Decimal(65)
		thumbfactor = Decimal(1) / Decimal(26)
		fingerprintfactor = Decimal(1) / Decimal(35080)
		if who is None:
			who = "5.5ft"
		who = isFeetAndInchesAndIfSoFixIt(who)
		whoin = who
		who = toSV(getnum(who), getlet(who))
		userarray = ["Raw\n", "Y\n", who, defaultheight, defaultweight, defaultdensity, "M\n", "None\n"]
		readableheight = fromSVacc(userarray[CHEI])
		readablefootheight = fromSVacc(Decimal(userarray[CHEI]) * footfactor)
		readablefootUSAheight = fromSVUSA(Decimal(userarray[CHEI]) * footfactor)
		readablefootthick = fromSVacc(Decimal(userarray[CHEI]) * footthickfactor)
		readablefootUSAthick = fromSVUSA(Decimal(userarray[CHEI]) * footthickfactor)
		readableUSAheight = fromSVUSA(userarray[CHEI])
		userbaseh = fromSV(userarray[BHEI])
		userbasehusa = fromSVUSA(userarray[BHEI])
		userbasew = fromWV(userarray[BWEI])
		userbasewusa = fromWVUSA(userarray[BWEI])
		density = Decimal(userarray[DENS])
		multiplier = Decimal(userarray[CHEI]) / Decimal(userarray[BHEI])
		basemult = Decimal(userarray[CHEI]) / Decimal(defaultheight)
		multipliercubed = multiplier**3
		basemultcubed = basemult**3
		baseweight = Decimal(userarray[BWEI])
		weightmath = (baseweight*(multipliercubed))*density
		readableweight = fromWV(weightmath)
		readableUSAweight = fromWVUSA(weightmath)
		normalheight = fromSVacc(Decimal(defaultheight)/Decimal(basemult))
		normalUSAheight = fromSVUSA(Decimal(defaultheight)/Decimal(basemult))
		normalweight = fromWV(Decimal(defaultweight)/Decimal(basemultcubed))
		normalUSAweight = fromWVUSA( Decimal(defaultweight) / Decimal(basemultcubed) )
		thumbsize = fromSVacc(Decimal(userarray[CHEI]) * thumbfactor)
		thumbsizeUSA = fromSVUSA(Decimal(userarray[CHEI]) * thumbfactor)
		footheight = Decimal(userarray[CHEI]) * footfactor
		footwidth = fromSV(Decimal(userarray[CHEI]) * footwidthfactor)
		footwidthUSA = fromSVUSA(Decimal(userarray[CHEI]) * footwidthfactor)
		footlengthinches = Decimal(userarray[CHEI]) * footfactor / inch
		shoesize = toShoeSize(footlengthinches)
		fingerprintdepth = fromSVacc(Decimal(userarray[CHEI]) * fingerprintfactor)
		fingerprintdepthUSA = fromSVUSA(Decimal(userarray[CHEI]) * fingerprintfactor)
		hcms = place_value(round(multiplier, 3))
		hbms = place_value(round(basemult, 3))
		wcms = place_value(round(multipliercubed * density, 3))
		wbms = place_value(round(basemultcubed * density, 3))
		if multiplier > 999999999999999:
			hcms = '{:.2e}'.format(multiplier)
		if basemult > 999999999999999:
			hbms = '{:.2e}'.format(basemult)
		if multipliercubed > 999999999999999:
			wcms = '{:.2e}'.format(multipliercubed * density)
		if basemultcubed > 999999999999999:
			wbms = '{:.2e}'.format(basemultcubed * density)

		await ctx.send("""**{0} Stats:**
	Current Height: {1} | {2} ({4}x normal)
	Current Weight: {5} | {6} ({8}x normal)
	Foot Length: {10} | {11} ({12})
	Foot Width: {13} | {14}
	Toe Height: {15} | {16}
	Thumb Size: {17} | {18}
	Fingerprint Depth: {23} | {24}
	Size of a Normal Man (Comparative) {19} | {20}
	Weight of a Normal Man (Comparative) {21} | {22}""".format(whoin, readableheight, readableUSAheight,
		hcms, hbms, readableweight, readableUSAweight,
		wcms, wbms, density, readablefootheight, readablefootUSAheight, shoesize,
		footwidth, footwidthUSA, readablefootthick, readablefootUSAthick,
		thumbsize, thumbsizeUSA,
		normalheight, normalUSAheight, normalweight, normalUSAweight,
		userbaseh, userbasehusa, userbasew, userbasewusa,
		fingerprintdepth, fingerprintdepthUSA).replace("<@Raw>", "**Raw**"))
		print("Stats for {0} sent.".format(who))
		pass

	@stats.error
	async def stats_handler(self, ctx, error):
		if isinstance(error, InvalidOperation):
			await ctx.send("""SizeBot cannot perform this action due to a math error.
	Are you too big, {0}?""".format(ctx.message.author.id))
		else:
			await ctx.send("""Error? {0}""".format(error))

	@statsraw.error
	async def statsraw_handler(self, ctx, error):
		if isinstance(error, InvalidOperation):
			await ctx.send("""SizeBot cannot perform this action due to a math error.
	Are you too big, {0}?""".format(ctx.message.author.id))
		else:
			await ctx.send("""Error? {0}""".format(error))

	@commands.command()
	async def compare(self, ctx, who : discord.Member = None, who2 : discord.Member = None):
		biguser = []
		biguserid = ""
		smalluser = []
		smalluserid = ""
		if who2 is None:
			who2 = ctx.message.author
		if who is None:
			await ctx.send("""Please use either two parameters to compare two people, or one to compare with yourself.""", delete_after=5)
		whoid = str(who.id)
		who2id = str(who2.id)
		if not os.path.exists(folder + '/users/' + whoid + '.txt'):
		#User file missing.
			await ctx.send("""Sorry! User isn't registered with SizeBot.
	To register, use the `&register` command.""", delete_after=5)
		if not os.path.exists(folder + '/users/' + who2id + '.txt'):
		#User file missing.
			await ctx.send("""Sorry! User isn't registered with SizeBot.
	To register, use the `&register` command.""", delete_after=5)
		else:
			userarray1 = read_user(whoid)
			userarray2 = read_user(who2id)
			if Decimal(userarray1[2]) == Decimal(userarray2[2]):
				await ctx.send("<@{0}> and <@{1}> match 1 to 1.".format(whoid, who2id))
			elif Decimal(userarray1[2]) > Decimal(userarray2[2]):
					biguser = userarray1
					biguserid = whoid
					smalluser = userarray2
					smalluserid = who2id
			else:
					biguser = userarray2
					biguserid = who2id
					smalluser = userarray1
					smalluserid = whoid
		#Compare.
		bch = Decimal(biguser[2])
		bbh = Decimal(biguser[3])
		sch = Decimal(smalluser[2])
		sbh = Decimal(smalluser[3])
		bbw = Decimal(biguser[4])
		sbw = Decimal(smalluser[4])
		bd = Decimal(biguser[5])
		sd = Decimal(smalluser[5])
		bigmult = bch / bbh
		smallmult = sch / sbh
		bcw = bbw * (bigmult ** 3) * bd
		scw = sbw * (smallmult ** 3) * sd
		diffmult = bigmult / smallmult
		b2sh = bbh * diffmult
		s2bh = sbh / diffmult
		b2sw = bbw * (diffmult ** 3)
		s2bw = sbw / (diffmult ** 3)
		bigtosmallheight = fromSVacc(b2sh)
		smalltobigheight = fromSVacc(s2bh)
		bigtosmallheightUSA = fromSVUSA(b2sh)
		smalltobigheightUSA = fromSVUSA(s2bh)
		bigtosmallfoot = fromSVacc(b2sh / 7)
		smalltobigfoot = fromSVacc(s2bh / 7)
		bigtosmallfootUSA = fromSVUSA(b2sh / 7)
		smalltobigfootUSA = fromSVUSA(s2bh / 7)
		bigtosmallshoe = toShoeSize(b2sh / 7 / inch)
		smalltobigshoe = toShoeSize(s2bh / 7 / inch)
		bigtosmallweight = fromWV(b2sw)
		smalltobigweight = fromWV(s2bw)
		bigtosmallweightUSA = fromWVUSA(b2sw)
		smalltobigweightUSA = fromWVUSA(s2bw)
		timestaller = place_value(round((bch / sch), 3))
		#Print compare.
		await ctx.send("""**Comparison:**
<@{0}> is really: {10} / {11} | {12} / {13}.
To <@{1}>, <@{0}> looks: {2} / {3} | {4} / {5}.
To <@{1}>, <@{0}>'s foot looks: {18} / {19} long. ({22})

<@{0}> is {24}x taller than <@{1}>.

<@{1}> is really: {14} / {15} | {16} / {17}
To <@{0}>, <@{1}> looks: {6} / {7} | {8} / {9}.
To <@{0}>, <@{1}>'s foot looks: {20} / {21} long. ({23})""".format(biguserid, smalluserid, bigtosmallheight, bigtosmallheightUSA,
 bigtosmallweight, bigtosmallweightUSA, smalltobigheight, smalltobigheightUSA, smalltobigweight, smalltobigweightUSA,
 fromSVacc(bch), fromSVUSA(bch), fromWV(bcw), fromWVUSA(bcw), fromSVacc(sch), fromSVUSA(sch), fromWV(scw), fromWVUSA(scw),
 bigtosmallfoot, bigtosmallfootUSA, smalltobigfoot, smalltobigfootUSA, bigtosmallshoe, smalltobigshoe, timestaller))
		print("Compared {0} and {1}".format(who, who2))
		pass

	@compare.error
	async def compare_handler(self, ctx, error):
		if isinstance(error, InvalidOperation):
			await ctx.send("""Math error? {0}?""".format(error))
		else:
			await ctx.send("""Error? {0}""".format(error))

	@commands.command()
	async def compareraw(self, ctx, who : str = None):
		biguser = []
		biguserid = ""
		smalluser = []
		smalluserid = ""
		if who is None:
			who = "5.5ft"
		who = isFeetAndInchesAndIfSoFixIt(who)
		who = toSV(getnum(who), getlet(who))
		userarray1 = read_user(ctx.message.author.id)
		userarray2 = ["Raw\n", "Y\n", who, defaultheight, defaultweight, defaultdensity, "M\n", "None\n"]
		if Decimal(userarray1[2]) == Decimal(userarray2[2]):
			await ctx.send("Users match 1 to 1.")
		elif Decimal(userarray1[2]) > Decimal(userarray2[2]):
			biguser = userarray1
			biguserid = ctx.message.author.id
			smalluser = userarray2
			smalluserid = "Raw"
		else:
			biguser = userarray2
			biguserid = "Raw"
			smalluser = userarray1
			smalluserid = ctx.message.author.id
		#Compare.
		bch = Decimal(biguser[2])
		bbh = Decimal(biguser[3])
		sch = Decimal(smalluser[2])
		sbh = Decimal(smalluser[3])
		bbw = Decimal(biguser[4])
		sbw = Decimal(smalluser[4])
		bd = Decimal(biguser[5])
		sd = Decimal(smalluser[5])
		bigmult = bch / bbh
		smallmult = sch / sbh
		bcw = bbw * (bigmult ** 3) * bd
		scw = sbw * (smallmult ** 3) * sd
		diffmult = bigmult / smallmult
		b2sh = bbh * diffmult
		s2bh = sbh / diffmult
		b2sw = bbw * (diffmult ** 3)
		s2bw = sbw / (diffmult ** 3)
		bigtosmallheight = fromSVacc(b2sh)
		smalltobigheight = fromSVacc(s2bh)
		bigtosmallheightUSA = fromSVUSA(b2sh)
		smalltobigheightUSA = fromSVUSA(s2bh)
		bigtosmallfoot = fromSVacc(b2sh / 7)
		smalltobigfoot = fromSVacc(s2bh / 7)
		bigtosmallfootUSA = fromSVUSA(b2sh / 7)
		smalltobigfootUSA = fromSVUSA(s2bh / 7)
		bigtosmallshoe = toShoeSize(b2sh / 7 / inch)
		smalltobigshoe = toShoeSize(s2bh / 7 / inch)
		bigtosmallweight = fromWV(b2sw)
		smalltobigweight = fromWV(s2bw)
		bigtosmallweightUSA = fromWVUSA(b2sw)
		smalltobigweightUSA = fromWVUSA(s2bw)
		timestaller = place_value(round((bch / sch), 3))
		#Print compare.
		await ctx.send("""**Comparison:**
<@{0}> is really: {10} / {11} | {12} / {13}.
To <@{1}>, <@{0}> looks: {2} / {3} | {4} / {5}.
To <@{1}>, <@{0}>'s foot looks: {18} / {19} long. ({22})

<@{0}> is {24}x taller than <@{1}>.

<@{1}> is really: {14} / {15} | {16} / {17}
To <@{0}>, <@{1}> looks: {6} / {7} | {8} / {9}.
To <@{0}>, <@{1}>'s foot looks: {20} / {21} long. ({23})""".format(biguserid, smalluserid, bigtosmallheight, bigtosmallheightUSA,
 bigtosmallweight, bigtosmallweightUSA, smalltobigheight, smalltobigheightUSA, smalltobigweight, smalltobigweightUSA,
 fromSVacc(bch), fromSVUSA(bch), fromWV(bcw), fromWVUSA(bcw), fromSVacc(sch), fromSVUSA(sch), fromWV(scw), fromWVUSA(scw),
 bigtosmallfoot, bigtosmallfootUSA, smalltobigfoot, smalltobigfootUSA, bigtosmallshoe, smalltobigshoe, timestaller).replace("<@Raw>", "**Raw**"))
		print("Compared {0} and {1}".format(ctx.message.author.name, who))
		pass

	@compareraw.error
	async def compareraw_handler(self, ctx, error):
		if isinstance(error, InvalidOperation):
			await ctx.send("""Math error? {0}?""".format(error))
		else:
			await ctx.send("""Error? {0}""".format(error))

#Necessary.
def setup(bot):
	bot.add_cog(StatsCog(bot))
