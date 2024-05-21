from typing import Annotated

import discord
from discord import Embed
from discord.ext import commands

from sizebot.lib import userdb
from sizebot.lib.errors import InvalidSizeValue
from sizebot.lib.types import BotContext
from sizebot.lib.utils import is_url


def _parse_url(s: str) -> str:
    if not is_url(s):
        raise InvalidSizeValue(f"{s} is not a valid URL.")
    return s


class ProfileCog(commands.Cog):
    """Profile commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        aliases = ["setpic"],
        usage = "<url>",
        category = "profile"
    )
    @commands.guild_only()
    async def setpicture(self, ctx: BotContext, *, url: Annotated[str, _parse_url]):
        """ Set your profile's image. Must be a valid image URL."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.picture_url = url
        userdb.save(userdata)
        await ctx.send("Profile image set.")

    @commands.command(
        aliases = ["setdesc"],
        usage = "<description...>",
        category = "profile",
        multiline = True
    )
    @commands.guild_only()
    async def setdescription(self, ctx: BotContext, *, desc: str):
        """Set your profile description.

        Accepts slightly more markdown than usual, see https://leovoel.github.io/embed-visualizer/"""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.description = desc
        userdb.save(userdata)
        await ctx.send("Profile description set.")

    @commands.command(
        aliases = ["clearpic", "unsetpic", "resetpic", "clearpicture", "unsetpicture"],
        category = "profile"
    )
    @commands.guild_only()
    async def resetpicture(self, ctx: BotContext):
        """Reset your profile's image."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.picture_url = None
        userdb.save(userdata)
        await ctx.send("Profile image reset.")

    @commands.command(
        aliases = ["cleardesc", "unsetdesc", "resetdesc", "cleardescription", "unsetdescription"],
        category = "profile"
    )
    @commands.guild_only()
    async def resetdescription(self, ctx: BotContext):
        """Remove your profile description."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id, allow_unreg=True)
        userdata.description = None
        userdb.save(userdata)
        await ctx.send("Profile description reset.")

    @commands.command(
        aliases = ["card"],
        usage = "[user]",
        category = "profile"
    )
    @commands.guild_only()
    async def profile(self, ctx: BotContext, member: discord.Member | None = None):
        """See the profile of you or another SizeBot user.

        #ALPHA#
        """
        if member is None:
            member = ctx.author
        same_user = ctx.author.id == member.id
        userdata = userdb.load(ctx.guild.id, member.id, member = member, allow_unreg=same_user)
        profileembed = Embed(title = userdata.nickname, description = userdata.description)
        profileembed.set_image(url = userdata.auto_picture_url)
        profileembed.add_field(name = "Height", value = f"{userdata.height:,.3mu}", inline = True)
        profileembed.add_field(name = "Weight", value = f"{userdata.weight:,.3mu}", inline = True)

        await ctx.send(embed = profileembed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ProfileCog(bot))
