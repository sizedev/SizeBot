from dataclasses import dataclass
from typing import Optional, Union

from PIL.Image import Image


@dataclass
class EmbedTemplate:
    title: str
    description: Optional[str] = None
    color: Union[tuple, int, None] = None
    image: Union[Image, str, None] = None
