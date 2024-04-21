import base64
from dataclasses import dataclass
import json
import importlib.resources as pkg_resources
from json.decoder import JSONDecodeError
from typing import Optional
import aiohttp
from aiohttp_requests import requests
import logging

import sizebot.data
from sizebot.conf import conf
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV
from sizebot.lib.userdb import User
from sizebot.lib.utils import url_safe

logger = logging.getLogger("sizebot")

model_heights = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))


def get_model_scale(model, view, height_in_meters):
    normal_height = Decimal(model_heights[model][view])
    return height_in_meters / normal_height


def get_entity_json(name, model, view, height, x):
    scale = get_model_scale(model, view, height)
    return {
        "name": model,
        "customName": name,
        "scale": float(scale),
        "view": view,
        "x": str(x),
        "y": "0",
        "priority": 0,
        "brightness": 1
    }


async def shorten_url(url):
    if not conf.cuttly_key:
        return url
    try:
        r = await requests.get(f"https://cutt.ly/api/api.php?key={conf.cuttly_key}&short={url}", raise_for_status=True)
    except aiohttp.ClientResponseError as e:
        logger.error(f"Unable to shorten url: Status {e.status}")
        return url
    try:
        cuttly_response = await r.json(content_type="text/html")
    except (aiohttp.ContentTypeError):
        logger.error(f"Unable to shorten url: Cannot parse JSON, bad content type: {r.content_type}")
        return url
    except (JSONDecodeError):
        logger.error("Unable to shorten url: Cannot parse JSON")
        return url
    short_url = cuttly_response["url"]["shortLink"]
    return short_url


@dataclass
class MacrovisionEntity():
    name: str
    model: str
    view: Optional[str]
    height: SV
    x: float = 0


def user_to_entity(u: User) -> MacrovisionEntity:
    return MacrovisionEntity(
        name=u.nickname,
        model=u.macrovision_model,
        view=u.macrovision_view,
        height=u.height
    )


def statbox_to_entity(s: StatBox) -> MacrovisionEntity:
    return MacrovisionEntity(
        name=s['nickname'].value,
        model=s['macrovision_model'].value,
        view=s['macrovision_view'].value,
        height=s['height'].value
    )


def get_url_from_users(users: list[User]) -> str:
    return get_url([user_to_entity(u) for u in users])


def get_url_from_statboxes(statboxes: list[StatBox]) -> str:
    return get_url([statbox_to_entity(s) for s in statboxes])


def get_url(entities: list[MacrovisionEntity]) -> str:
    if len(entities) <= 0:
        raise ValueError("At least one person is required")

    entities.sort(key=lambda e: e.height, reverse=True)

    world_height = entities[0].height

    x_offset = Decimal(0)
    for p in entities:
        p.name = url_safe(p.name)
        # Backwards compatibility
        if p.view is None:
            p.view = p.model
            p.model = "Human"
        p.x = x_offset
        x_offset += p.height / 4

    entities_json = [get_entity_json(e.name, e.model, e.view, e.height, e.x) for e in entities]

    url_json = {
        "entities": entities_json,
        "world": {
            "height": float(world_height),
            "unit": "meters",
            "x": 0,
            "y": 0
        },
        "version": 3
    }
    json_string = json.dumps(url_json)
    json_bytes = json_string.encode("utf-8")
    base64_bytes = base64.b64encode(json_bytes)
    base64_string = base64_bytes.decode("ascii")
    url = f"https://macrovision.crux.sexy/?scene={base64_string}"
    return url
