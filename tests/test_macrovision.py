from sizebot.lib.decimal import Decimal
from sizebot.lib import macrovision


def test_macrovision():
    assert macrovision.get_url([
        {
            "name": "Duncan",
            "model": "man1",
            "height": Decimal("0.0127")
        },
        {
            "name": "Natalie",
            "model": "woman1",
            "height": Decimal("0.1524")
        }
    ]) == "https://macrovision.crux.sexy/?scene=eyJlbnRpdGllcyI6IFt7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJOYXRhbGllIiwgInNjYWxlIjogMC4wODk1NTIyMzg4MDU5NzAxNCwgInZpZXciOiAid29tYW4xIiwgIngiOiAiMCIsICJ5IjogIjAiLCAicHJpb3JpdHkiOiAwLCAiYnJpZ2h0bmVzcyI6IDF9LCB7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJEdW5jYW4iLCAic2NhbGUiOiAwLjAwNzA0MjI1MzUyMTEyNjc2MSwgInZpZXciOiAibWFuMSIsICJ4IjogIjAuMDM4MSIsICJ5IjogIjAiLCAicHJpb3JpdHkiOiAwLCAiYnJpZ2h0bmVzcyI6IDF9XSwgIndvcmxkIjogeyJoZWlnaHQiOiAwLjE1MjQsICJ1bml0IjogIm1ldGVycyIsICJ4IjogIjAiLCAieSI6ICIwIn0sICJ2ZXJzaW9uIjogM30="