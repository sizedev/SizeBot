from discord.ext import commands
import digilogger as logger

# TODO: Make these lists different for big and small.
gifts = ["a shrink potion",
        "a growth potion",
        "a size gun",
        "a doll house"]

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
        output += f"It was... **{usergift}!**"
        if userid in alreadyclaimed:
            output += "\n*Opening the gift again doesn't change what's inside it!*"
        await ctx.send(output)
        alreadyclaimed.append(userid)
