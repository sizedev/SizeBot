import json
import base64

import pytest

from sizebot.lib import macrovision, units
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import SV


units.init()


def json_to_base64(j):
    json_string = json.dumps(j)
    json_bytes = json_string.encode("utf-8")
    base64_bytes = base64.b64encode(json_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


@pytest.mark.asyncio
async def test_macrovision():
    expected_base64 = json_to_base64({
        "entities": [
            {"name": "Human", "customName": "Natalie", "scale": 0.08955223880597014, "view": "woman1", "x": "0", "y": "0", "priority": 0, "brightness": 1},
            {"name": "Human", "customName": "Duncan", "scale": 0.00704225352112676, "view": "man1", "x": "0.0381", "y": "0", "priority": 0, "brightness": 1}
        ],
        "world": {"height": 0.1524, "unit": "meters", "x": 0, "y": 0},
        "version": 3
    })
    expected_url = f"https://macrovision.crux.sexy/?scene={expected_base64}"
    macrovision_url = await macrovision.get_url(
        [
            {"name": "Duncan", "model": "man1", "height": Decimal("0.0127")},
            {"name": "Natalie", "model": "woman1", "height": Decimal("0.1524")}
        ],
        shorten = False
    )
    assert macrovision_url == expected_url


@pytest.mark.asyncio
async def test_macrovision_SV():
    expected_base64 = json_to_base64({
        "entities": [
            {"name": "Human", "customName": "Natalie", "scale": 0.08955223880597014, "view": "woman1", "x": "0", "y": "0", "priority": 0, "brightness": 1},
            {"name": "Human", "customName": "Duncan", "scale": 0.00704225352112676, "view": "man1", "x": "0.0381", "y": "0", "priority": 0, "brightness": 1}
        ],
        "world": {"height": 0.1524, "unit": "meters", "x": 0, "y": 0},
        "version": 3
    })
    expected_url = f"https://macrovision.crux.sexy/?scene={expected_base64}"
    macrovision_url = await macrovision.get_url(
        [
            {"name": "Duncan", "model": "man1", "height": SV.parse("0.5in")},
            {"name": "Natalie", "model": "woman1", "height": SV.parse("6in")}
        ],
        shorten = False
    )
    assert macrovision_url == expected_url


@pytest.mark.asyncio
async def test_weird_names():
    expected_base64 = json_to_base64({
        "entities": [
            {"name": "Human", "customName": r"r'(?<!\.)[.?!](?!\.)', z [1.22m]", "scale": 0.675945436397915, "view": "man1", "x": "0", "y": "0", "priority": 0, "brightness": 1},
            {"name": "Human", "customName": "Natalie", "scale": 0.08955223880597014, "view": "woman1", "x": "0.30475", "y": "0", "priority": 0, "brightness": 1}
        ],
        "world": {"height": 1.219, "unit": "meters", "x": 0, "y": 0},
        "version": 3
    })
    expected_url = f"https://macrovision.crux.sexy/?scene={expected_base64}"
    macrovision_url = await macrovision.get_url(
        [
            {"name": r"r'(?<!\.)[.?!](?!\.)', z [1.22m]", "model": "man1", "height": Decimal("1.219")},
            {"name": "Natalie", "model": "woman1", "height": Decimal("0.1524")}
        ],
        shorten = False
    )
    assert macrovision_url == expected_url
