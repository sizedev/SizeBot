from discord import Embed

old_add_field = Embed.add_field


def add_field(self: Embed, *, name: str = None, value: str = None, inline: bool = True) -> Embed:
    if not name:
        name = "\u200b"
    if not value:
        value = "\u200b"

    return old_add_field(self, name=name, value=value, inline=inline)


def patch():
    Embed.add_field = add_field
