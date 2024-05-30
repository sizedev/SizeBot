from typing import Any

import json
import base64

import pytest

from sizebot.lib import macrovision, units
from sizebot.lib.units import SV


units.init()


def json_to_base64(j: Any) -> str:
    json_string = json.dumps(j)
    json_bytes = json_string.encode("utf-8")
    base64_bytes = base64.b64encode(json_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


@pytest.mark.asyncio
async def test_macrovision():
    expected_base64 = json_to_base64({
        "entities": [
            {"name": "Human", "customName": "Natalie", "scale": 0.08955223880597014, "view": "female", "x": "0", "y": "0", "priority": 0, "brightness": 1},
            {"name": "Human", "customName": "Duncan", "scale": 0.00704225352112676, "view": "male", "x": "0.0381", "y": "0", "priority": 0, "brightness": 1}
        ],
        "world": {"height": 0.1524, "unit": "meters", "x": 0, "y": 0},
        "version": 3
    })
    expected_url = f"https://macrovision.crux.sexy/?scene={expected_base64}"
    macrovision_url = macrovision.get_url(
        [
            macrovision.MacrovisionEntity(name="Duncan", model="male", view=None, height=SV("0.0127")),
            macrovision.MacrovisionEntity(name="Natalie", model="female", view=None, height=SV("0.1524"))
        ]
    )
    assert macrovision_url == expected_url


@pytest.mark.asyncio
async def test_weird_names():
    expected_base64 = json_to_base64({
        "entities": [
            {"name": "Human", "customName": r"r'(?<!\.)[.?!](?!\.)', z [1.22m]", "scale": 0.675945436397915, "view": "male", "x": "0", "y": "0", "priority": 0, "brightness": 1},
            {"name": "Human", "customName": "Natalie", "scale": 0.08955223880597014, "view": "female", "x": "0.30475", "y": "0", "priority": 0, "brightness": 1}
        ],
        "world": {"height": 1.219, "unit": "meters", "x": 0, "y": 0},
        "version": 3
    })
    expected_url = f"https://macrovision.crux.sexy/?scene={expected_base64}"
    macrovision_url = macrovision.get_url(
        [
            macrovision.MacrovisionEntity(name=r"r'(?<!\.)[.?!](?!\.)', z [1.22m]", model="male", view=None, height=SV("1.219")),
            macrovision.MacrovisionEntity(name="Natalie", model="female", view=None, height=SV("0.1524"))
        ]
    )
    assert macrovision_url == expected_url
