from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sizebot.lib.userdb import User


import base64
from dataclasses import dataclass
import json
import importlib.resources as pkg_resources

import sizebot.data
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV
from sizebot.lib.utils import url_safe

_model_heights = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))


def _get_model_scale(model: str, view: str, height_in_meters: SV) -> Decimal:
    normal_height = Decimal(_model_heights[model][view])
    return height_in_meters / normal_height


def _get_entity_json(name: str, model: str, view: str, height: SV, x: float) -> Any:
    scale = _get_model_scale(model, view, height)
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


@dataclass
class MacrovisionEntity():
    name: str
    model: str
    view: str | None
    height: SV
    x: float = 0


def _user_to_entity(u: User) -> MacrovisionEntity:
    return MacrovisionEntity(
        name=u.nickname,
        model=u.macrovision_model,
        view=u.macrovision_view,
        height=u.height
    )


def _statbox_to_entity(s: StatBox) -> MacrovisionEntity:
    return MacrovisionEntity(
        name=s['nickname'].value,
        model=s['macrovision_model'].value,
        view=s['macrovision_view'].value,
        height=s['height'].value
    )


def get_url_from_users(users: list[User]) -> str:
    return get_url([_user_to_entity(u) for u in users])


def get_url_from_statboxes(statboxes: list[StatBox]) -> str:
    return get_url([_statbox_to_entity(s) for s in statboxes])


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

    entities_json = [_get_entity_json(e.name, e.model, e.view, e.height, e.x) for e in entities]

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


def is_model(model: str) -> bool:
    return model in _model_heights


def is_modelview(model: str, view: str) -> bool:
    return model in _model_heights and view in _model_heights[model]
