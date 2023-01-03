import logging
import random
import typing

import discord
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.fakeplayer import FakePlayer
from sizebot.lib.pokemon import pokemon
from sizebot.lib.units import SV
from sizebot.lib.versioning import release_on

logger = logging.getLogger("sizebot")


class PokemonCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @release_on("3.7")
    @commands.command(
        aliases = ["dex"],
        category = "objects"
    )
    async def pokedex(self, ctx, pkmn: typing.Union[int, str] = None):
        """Pokemaaaaaaaaans"""
        if isinstance(pkmn, str):
            p = next((m for m in pokemon if m.name.lower() == pkmn.lower()), None)
        elif isinstance(pkmn, int):
            p = next((m for m in pokemon if m.natdex == pkmn), None)
        else:
            p = None

        if p is None:
            p = random.choice(pokemon)

        e = p.stats_embed()
        await ctx.send(embed = e)

    @release_on("3.7")
    @commands.command(
        aliases = ["pokecompare", "pokecomp", "lookatpoke"],
        category = "objects"
    )
    async def lookatpokemon(self, ctx, pkmn: typing.Union[int, str] = None, *, who: typing.Union[discord.Member, FakePlayer, SV] = None):
        """Pokemaaaaaaaaans"""
        if who is None:
            who = ctx.author

        userdata = userdb.load_or_fake(who)

        if isinstance(pkmn, str):
            p = next((m for m in pokemon if m.name.lower() == pkmn.lower()), None)
        elif isinstance(pkmn, int):
            p = next((m for m in pokemon if m.natdex == pkmn), None)
        else:
            p = None

        if p is None:
            p = random.choice(pokemon)

        e = p.comp_embed(user = userdata)
        await ctx.send(embed = e)


async def setup(bot):
    await bot.add_cog(PokemonCog(bot))
