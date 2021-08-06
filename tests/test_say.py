import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sizebot.lib.units import SV
from sizebot.lib.errors import UserNotFoundException
from sizebot.conf import conf
conf.load()     # Need to run this before importing anything from sizebot.cog

from sizebot.cogs import say   # noqa: E402


@pytest.fixture
def ctx():
    ctx = AsyncMock()
    ctx.guild.id = 1
    ctx.author.id = 2
    ctx.author.display_name = "defaultboi"
    return ctx


@pytest.fixture
def userdb_load():
    with patch("sizebot.lib.userdb.load") as userdb_load:
        userdb_load.defaultheight = SV("1.754")
        yield userdb_load


@pytest.mark.asyncio
async def test_say_n3(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("0.001"), nickname="smollestboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("smollestboi whispers: \n> ...... ......")


@pytest.mark.asyncio
async def test_say_n2(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("0.008"), nickname="smollerboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("smollerboi squeaks: \n> ʰᵉˡˡᵒ, ʷᵒʳˡᵈ!")


@pytest.mark.asyncio
async def test_say_n1(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("0.1"), nickname="smolboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("smolboi murmurs: \n> ᴴᵉˡˡᵒ, ᵂᵒʳˡᵈ!")


@pytest.mark.asyncio
async def test_say_p0(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("2"), nickname="boi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("boi says: \n> Hello, World!")


@pytest.mark.asyncio
async def test_say_p1(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("20"), nickname="tolboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("tolboi shouts: \n> **Hello, World!**")


@pytest.mark.asyncio
async def test_say_p2(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("200"), nickname="tollerboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("tollerboi roars: \n> **Hᴇʟʟᴏ, Wᴏʀʟᴅ!**")


@pytest.mark.asyncio
async def test_say_p3(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("2000"), nickname="tollestboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("tollestboi booms: \n> :regional_indicator_h::regional_indicator_e::regional_indicator_l::regional_indicator_l::regional_indicator_o::arrow_up_small:<:blank:665063842866397185>:regional_indicator_w::regional_indicator_o::regional_indicator_r::regional_indicator_l::regional_indicator_d::exclamation:")


@pytest.mark.asyncio
async def test_say_default(ctx, userdb_load):
    userdb_load.side_effect = UserNotFoundException(1, 2)
    await say.SayCog.say(None, ctx, message="Hello, World!")
    userdb_load.assert_called_with(1, 2)
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("defaultboi says: \n> Hello, World!")
