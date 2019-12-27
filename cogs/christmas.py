from discord.ext import commands
import digilogger as logger

with open("gifts.txt") as f:
    gifts = f.readlines()
gifts = [x.strip() for x in gifts]

alreadyclaimed = set()


# It's Christmas time!
class ChristmasCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def secretsanta(self, ctx):
        userid = ctx.message.author.id
        usergift = gifts[userid % len(gifts)]
        output = f"<@{userid}> opened up their Secret Santa gift...\n"
        output += f"It was... {usergift}"
        if userid in alreadyclaimed:
            output += "\n*Opening the gift again doesn't change what's inside it!*"
        await ctx.send(output)
        logger.msg(f"{ctx.message.author.id}/{ctx.message.author.nick} opened their gift!")
        alreadyclaimed.add(userid)


#Necessary.
def setup(bot):
    bot.add_cog(ChristmasCog(bot))
