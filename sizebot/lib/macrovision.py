import base64
import json
from operator import itemgetter

from sizebot.lib.decimal import Decimal


model_heights = {
    "man1": Decimal("1.8034"),
    "woman1": Decimal("1.7018")
}


def get_model_scale(model, height_in_meters):
    normal_height = model_heights[model]
    return height_in_meters / normal_height


def get_entity_json(name, model, height, x):
    scale = get_model_scale(model, height)
    return {
        "name": "Human",
        "customName": name,
        "scale": float(scale),
        "view": model,
        "x": str(x),
        "y": "0",
        "priority": 0,
        "brightness": 1
    }


def get_url(people):
    """Accepts an array of dictionary objects with 'model', 'name', and 'height' properties"""
    if len(people) <= 0:
        raise ValueError("At least one person is required")

    people.sort(key=itemgetter(2), reverse=True)

    world_height = people[0][2]

    entities = []
    x_offset = Decimal(0)
    for p in people:
        name, model, height = p
        entities.append(get_entity_json(name, model, height, x_offset))
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
