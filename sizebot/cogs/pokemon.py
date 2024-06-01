import logging
import random

from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.pokemon import pokemon
from sizebot.lib.types import BotContext, GuildContext
from sizebot.lib.userdb import MemberOrFakeOrSize

logger = logging.getLogger("sizebot")


class PokemonCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["dex"],
        category = "objects"
    )
    async def pokedex(self, ctx: BotContext, pkmn: int | str = None):
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

    @commands.command(
        aliases = ["pokecompare", "pokecomp", "lookatpoke"],
        category = "objects"
    )
    @commands.guild_only()
    async def lookatpokemon(self, ctx: GuildContext, pkmn: int | str = None, *, who: MemberOrFakeOrSize = None):
        """Pokemaaaaaaaaans"""
        if who is None:
            who = ctx.author

        userdata = userdb.load_or_fake(who)

        if pkmn == "lad":
            pkmn = "kricketot"

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


async def setup(bot: commands.Bot):
    await bot.add_cog(PokemonCog(bot))
