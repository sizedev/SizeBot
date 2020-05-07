import discord


class Embed(discord.Embed):
    def add_field(self, *, name=None, value=None, inline=True):
        if not name:
            name = "\u200b"
        if not value:
            value = "\u200b"

        return super().add_field(name=name, value=value, inline=inline)
