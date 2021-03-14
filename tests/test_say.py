import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sizebot.cogs import say
from sizebot.lib.units import SV


@pytest.fixture
def ctx():
    mock = AsyncMock()
    return mock


@pytest.fixture
def userdb_load():
    with patch("sizebot.lib.userdb.load") as userdb_load:
        yield userdb_load


@pytest.mark.asyncio
async def test_say_smollest(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("0.001"), nickname="smollestboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("smollestboi whispers: \n> ...... ......")


@pytest.mark.asyncio
async def test_say_smoller(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("0.008"), nickname="smollerboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("smollerboi squeaks: \n> ʰᵉˡˡᵒ, ʷᵒʳˡᵈ!")


@pytest.mark.asyncio
async def test_say_smol(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("0.1"), nickname="smolboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("smolboi murmurs: \n> ᴴᵉˡˡᵒ, ᵂᵒʳˡᵈ!")


@pytest.mark.asyncio
async def test_say_normal(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("2"), nickname="boi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("boi says: \n> Hello, World!")


@pytest.mark.asyncio
async def test_say_tol(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("20"), nickname="tolboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("tolboi shouts: \n> **Hello, World!**")


@pytest.mark.asyncio
async def test_say_toller(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("200"), nickname="tollerboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("tollerboi roars: \n> **Hᴇʟʟᴏ, Wᴏʀʟᴅ!**")


@pytest.mark.asyncio
async def test_say_tollest(ctx, userdb_load):
    userdb_load.return_value = MagicMock(height=SV("2000"), nickname="tollestboi")
    await say.SayCog.say(None, ctx, message="Hello, World!")
    ctx.message.delete.assert_called_with(delay=0)
    ctx.send.assert_called_with("tollestboi booms: \n> :regional_indicator_h::regional_indicator_e::regional_indicator_l::regional_indicator_l::regional_indicator_o::arrow_up_small:<:blank:665063842866397185>:regional_indicator_w::regional_indicator_o::regional_indicator_r::regional_indicator_l::regional_indicator_d::exclamation:")
