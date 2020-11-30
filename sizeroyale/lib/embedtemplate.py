import io
from dataclasses import dataclass
from typing import Optional, Union

import arrow
from PIL.Image import Image

from discord import File
from sizebot.discordplus.embed import Embed

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
        e = Embed(title = self.title,
                  description = self.description,
                  color = self.color)
        if self.image:
            i = img_to_file(self.image, name = 
            "royale-" + arrow.now().timestamp + ".png")
            e.set_image(i)

        return e
