import discord

from sizebot.lib import telemetry


def setup(bot):
    @bot.listen
    def on_command(ctx):
        # Log command runs to telemetry
        telemetry.CommandRun(str(ctx.invoked_with)).save()

        member = ctx.author
        isMember = isinstance(member, discord.Member)
        if not isMember:
            return True
        isGuildBanned = discord.utils.get(member.roles, name = "SizeBot_Banned") is not None
        return not isGuildBanned
