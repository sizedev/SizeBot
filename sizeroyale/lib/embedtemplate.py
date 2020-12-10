import io
from dataclasses import dataclass
from typing import Optional, Union

import arrow
from PIL.Image import Image

from discord import Embed, File


def img_to_file(i, name="file.png", format="PNG"):
    b = io.BytesIO()
    i.save(b, format)
    b.seek(0)
    f = File(b, name)
    return f


@dataclass
class EmbedTemplate:
    title: str
    description: Optional[str] = None
    color: Union[tuple, int, None] = None
    image: Union[Image, str, None] = None

    def to_embed(self):
        NOTHING = "\u200b"
        d = NOTHING if self. description is None else self.description
        c = Embed.Empty if self.color is None else self.color
        e = Embed(title = self.title,
                  description = d,
                  color = c)
        if self.image:
            imagename = "royale-" + str(arrow.now().timestamp) + ".png"
            i = img_to_file(self.image, name = imagename)
            e.set_image(url = f"attachment://{imagename}")
        else:
            i = None

        return (e, i)
