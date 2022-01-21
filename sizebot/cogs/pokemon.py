import logging
import random

from discord.ext import commands

from sizebot.lib.pokemon import pokemon

logger = logging.getLogger("sizebot")


class PokemonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["pkmn"],
        category = "objects"
    )
    async def pokemon(self, ctx):
        """Pokemaaaaaaaaans"""
        p = random.choice(pokemon)
        e = p.stats_embed()
        await ctx.send(embed = e)


def setup(bot):
    bot.add_cog(PokemonCog(bot))
