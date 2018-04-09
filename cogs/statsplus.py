import discord
from discord.ext import commands
from globalsb import *

class StatsPlusCog:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def statsplusshow(self, ctx, who : discord.Member = None):
    #Shows the extra stats of a user.
        await ctx.message.delete()
        await ctx.send("Beta!")
        if who is None:
            who = ctx.message.author
        whoid = str(who.id)
        if not os.path.exists(folder + '/plus/' + whoid + '.txt'):
        #User file missing.
            await ctx.send("""Sorry! User isn't registered for *Stats+*. 
    To register, use the `&statsplus help` command.""", delete_after=5)
        userarray = read_user(whoid)
        plusarray = read_user_plus(whoid)
        density = Decimal(userarray[DENS])
        multiplier = Decimal(userarray[CHEI]) / Decimal(userarray[BHEI])
        basemult = Decimal(userarray[CHEI]) / Decimal(defaultheight)
        multipliercubed = multiplier**3
        basemultcubed = basemult**3
        output = "**{0} Stats+:**".format(who.nick)
        if plusarray[BUST] != "None":
            oneboob = toWV((((8.34286 * plusarray[BUST]**2) + (130.82 * plusarray[BUST]) + 108.98) / 2)
                * (multipliercubed) * density * 1000)
            boobprotrusion = toSV(int(plusarray[BUST]) * multiplier * inch)
            output = output + """{0} is sporting {1}-cup breasts.
            One of their breasts weighs {2}, and adds {3} to their chest's circumfrence.\n""".format(who.nick,
                fromCV(plusarray[BUST]), oneboob, boobprotrusion)
        if plusarray[PNIS] != "None":
            penislength = int(plusarray[PNIS]) * multiplier
            output = output + "{0} is equipped with a {1} penis.\n".format(who.nick, penislength)
        if plusarray[FOOT] != "None":
            footlength = toSV(int(plusarray[FOOT]) * multiplier)
            shoesize = toShoeSize(int(plusarray[FOOT]) * multiplier)
            output = output + "{0} wears {1} shoes for their {1}-long feet.\n".format(who.nick, shoesize, footlength)
        await ctx.send(output)

    @commands.command()
    async def statsplus(self, ctx, operation : str, item : str = None, size : str = None):
    #Shows the extra stats of a user.
        await ctx.message.delete()
        await ctx.send("Beta!")


#Necessary.
def setup(bot):
    bot.add_cog(StatsPlusCog(bot))