import base64
import json
import importlib.resources as pkg_resources
from operator import itemgetter

import sizebot.data
from sizebot.lib.decimal import Decimal


model_heights = json.loads(pkg_resources.read_text(sizebot.data, "models.json"))


def get_model_scale(model, view, height_in_meters):
    normal_height = model_heights[model][view]
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


def get_url(people):
    """Accepts an array of dictionary objects with 'model', 'name', and 'height' properties"""
    if len(people) <= 0:
        raise ValueError("At least one person is required")

    people.sort(key=itemgetter("height"), reverse=True)

    world_height = people[0]["height"]

    entities = []
    x_offset = Decimal(0)
    for p in people:
        name, model, view, height = p["name"], p["model"], p.get("view"), p["height"]
        # Backwards compatibility
        if view is None:
            view = model
            model = "Human"
        entities.append(get_entity_json(name, model, view, height, x_offset))
        # A crude width estimate for now
        x_offset += height / 4

    url_json = {
        "entities": entities,
        "world": {
            "height": float(world_height),
            "unit": "meters",
            "x": "0",
            "y": "0"
        },
        "version": 3
    }
    json_string = json.dumps(url_json)
    json_bytes = json_string.encode("utf-8")
    base64_bytes = base64.b64encode(json_bytes)
    base64_string = base64_bytes.decode("ascii")
    return f"https://macrovision.crux.sexy/?scene={base64_string}"
