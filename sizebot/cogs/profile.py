import discord
from discord import Embed
from discord.ext import commands

from sizebot.lib import userdb


class ProfileCog(commands.Cog):
    """Profile commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        aliases = ["setpic"],
        usage = "<url>",
        category = "profile"
    )
    async def setpicture(self, ctx, *, url):
        """ Set your profile's image. Must be a valid image URL."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.picture_url = url
        userdb.save(userdata)
        await ctx.send("Profile image set.")

    @commands.command(
        aliases = ["setdesc"],
        usage = "<description...>",
        category = "profile"
    )
    async def setdescription(self, ctx, *, desc):
        """Set your profile description.

        Accepts slightly more markdown than usual, see https://leovoel.github.io/embed-visualizer/"""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.description = desc
        userdb.save(userdata)
        await ctx.send("Profile description set.")

    @commands.command(
        aliases = ["clearpic", "unsetpic", "resetpic", "clearpicture", "unsetpicture"],
        category = "profile"
    )
    async def resetpicture(self, ctx):
        """Reset your profile's image."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.picture_url = None
        userdb.save(userdata)
        await ctx.send("Profile image reset.")

    @commands.command(
        aliases = ["cleardesc", "unsetdesc", "resetdesc", "cleardescription", "unsetdescription"],
        category = "profile"
    )
    async def resetdescription(self, ctx):
        """Remove your profile description."""
        userdata = userdb.load(ctx.guild.id, ctx.author.id)
        userdata.description = None
        userdb.save(userdata)
        await ctx.send("Profile description reset.")

    @commands.command(
        aliases = ["pokedex"],
        usage = "[user]",
        category = "profile"
    )
    async def profile(self, ctx, member: discord.Member = None):
        """See the profile of you or another SizeBot user."""
        if member is None:
            member = ctx.author
        userdata = userdb.load(ctx.guild.id, member.id, member = member)
        profileembed = Embed(title = userdata.nickname, description = userdata.description)
        profileembed.set_image(url = userdata.auto_picture_url)
        profileembed.add_field(name = "Height", value = f"{userdata.height:,.3mu}", inline = True)
        profileembed.add_field(name = "Weight", value = f"{userdata.weight:,.3mu}", inline = True)

        await ctx.send(embed = profileembed)


def setup(bot):
    bot.add_cog(ProfileCog(bot))
