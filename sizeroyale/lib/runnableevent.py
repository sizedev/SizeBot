from typing import Optional

from PIL.Image import Image


class RunnableEvent:
    def __init__(self, text: str, players: Optional[list] = None,
                 deaths: Optional[list] = None, image: Optional[Image] = None):
        self.text = text
        self.players = players if players else []
        self.deaths = deaths if deaths else []
        self.image = image if image else None
