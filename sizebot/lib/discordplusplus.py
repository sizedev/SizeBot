from typing import Self

from discord import Embed as RawEmbed

class Embed(RawEmbed):
    def add_field(self, *, name: str | None = None, value: str | None = None, inline: bool = True) -> Self:
        if name is None:
            name = "\u200b"
        if value is None:
            value = "\u200b"

        return super().add_field(name=name, value=value, inline=inline)
