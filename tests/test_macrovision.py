import pytest

from sizebot.lib import macrovision, units
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV

units.init()

@pytest.mark.asyncio
async def test_macrovision():
    assert await macrovision.get_url([
        {"name": "Duncan", "model": "man1", "height": Decimal("0.0127")},
        {"name": "Natalie", "model": "woman1", "height": Decimal("0.1524")}
    ], shorten = False) == "https://macrovision.crux.sexy/?scene=eyJlbnRpdGllcyI6IFt7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJOYXRhbGllIiwgInNjYWxlIjogMC4wODk1NTIyMzg4MDU5NzAxNCwgInZpZXciOiAid29tYW4xIiwgIngiOiAiMCIsICJ5IjogIjAiLCAicHJpb3JpdHkiOiAwLCAiYnJpZ2h0bmVzcyI6IDF9LCB7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJEdW5jYW4iLCAic2NhbGUiOiAwLjAwNzA0MjI1MzUyMTEyNjc2LCAidmlldyI6ICJtYW4xIiwgIngiOiAiMC4wMzgxIiwgInkiOiAiMCIsICJwcmlvcml0eSI6IDAsICJicmlnaHRuZXNzIjogMX1dLCAid29ybGQiOiB7ImhlaWdodCI6IDAuMTUyNCwgInVuaXQiOiAibWV0ZXJzIiwgIngiOiAiMCIsICJ5IjogIjAifSwgInZlcnNpb24iOiAzfQ=="

@pytest.mark.asyncio
async def test_macrovision_SV():
    assert await macrovision.get_url([
        {"name": "Duncan", "model": "man1", "height": SV.parse("0.5in")},
        {"name": "Natalie", "model": "woman1", "height": SV.parse("6in")}
    ], shorten = False) == "https://macrovision.crux.sexy/?scene=eyJlbnRpdGllcyI6IFt7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJOYXRhbGllIiwgInNjYWxlIjogMC4wODk1NTIyMzg4MDU5NzAxNCwgInZpZXciOiAid29tYW4xIiwgIngiOiAiMCIsICJ5IjogIjAiLCAicHJpb3JpdHkiOiAwLCAiYnJpZ2h0bmVzcyI6IDF9LCB7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJEdW5jYW4iLCAic2NhbGUiOiAwLjAwNzA0MjI1MzUyMTEyNjc2LCAidmlldyI6ICJtYW4xIiwgIngiOiAiMC4wMzgxIiwgInkiOiAiMCIsICJwcmlvcml0eSI6IDAsICJicmlnaHRuZXNzIjogMX1dLCAid29ybGQiOiB7ImhlaWdodCI6IDAuMTUyNCwgInVuaXQiOiAibWV0ZXJzIiwgIngiOiAiMCIsICJ5IjogIjAifSwgInZlcnNpb24iOiAzfQ=="

@pytest.mark.asyncio
async def test_weird_names():
    assert await macrovision.get_url([
        {"name": r"r'(?<!\.)[.?!](?!\.)', z [1.22m]", "model": "man1", "height": Decimal("1.219")},
        {"name": "Natalie", "model": "woman1", "height": Decimal("0.1524")}
    ], shorten = False) == "https://macrovision.crux.sexy/?scene=eyJlbnRpdGllcyI6IFt7Im5hbWUiOiAiSHVtYW4iLCAiY3VzdG9tTmFtZSI6ICJyJyg/PCFcXC4pWy4/IV0oPyFcXC4pJywgeiBbMS4yMm1dIiwgInNjYWxlIjogMC42NzU5NDU0MzYzOTc5MTUsICJ2aWV3IjogIm1hbjEiLCAieCI6ICIwIiwgInkiOiAiMCIsICJwcmlvcml0eSI6IDAsICJicmlnaHRuZXNzIjogMX0sIHsibmFtZSI6ICJIdW1hbiIsICJjdXN0b21OYW1lIjogIk5hdGFsaWUiLCAic2NhbGUiOiAwLjA4OTU1MjIzODgwNTk3MDE0LCAidmlldyI6ICJ3b21hbjEiLCAieCI6ICIwLjMwNDc1IiwgInkiOiAiMCIsICJwcmlvcml0eSI6IDAsICJicmlnaHRuZXNzIjogMX1dLCAid29ybGQiOiB7ImhlaWdodCI6IDEuMjE5LCAidW5pdCI6ICJtZXRlcnMiLCAieCI6ICIwIiwgInkiOiAiMCJ9LCAidmVyc2lvbiI6IDN9"
