from discord import Embed

old_add_field = Embed.add_field


def add_field(self, *, name=None, value=None, inline=True):
    if not name:
        name = "\u200b"
    if not value:
        value = "\u200b"

    return old_add_field(self, name=name, value=value, inline=inline)


def patch():
    Embed.add_field = add_field
