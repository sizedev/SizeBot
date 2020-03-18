from discord.ext import tasks, commands

colorlist = [0xff0000, 0xff7700, 0xffff00, 0x00ff00, 0x00ffff, 0x0000ff, 0xff00ff]


class RainbowCog(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.rainbower.start()

    def cog_unload(self):
        self.rainbower.cancel()

    @tasks.loop(seconds=1.0)
    async def rainbower(self):
        self.index += 1
        if self.index >= 7:
            self.index == 0
        for guild in self.bot.guilds:
            for role in guild.roles:
                if role.name.lower() == "Rainbow":
                    await role.edit(color = colorlist[self.index])


def setup(bot):
    bot.add_cog(RainbowCog(bot))