import base64
import json
from operator import itemgetter

#from sizebot.lib.decimal import Decimal
from decimal import Decimal


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
    """Accepts an array of dictionary objects with 'model' and 'height' properties"""
    if len(people) <= 0:
        raise ValueError("At least one person is required")

    people.sort(key=itemgetter("height"), reverse=True)

    world_height = people[0]["height"]

    entities = []
    x_offset = Decimal(0)
    for p in people:
        name, model, height = p["name"], p["model"], p["height"]
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
    url_json_text = json.dumps(url_json)
    encoded = base64.urlsafe_b64encode(url_json_text.encode("ascii")).decode('ascii')
    return f"https://macrovision.crux.sexy/?scene={encoded}"


if __name__ == "__main__":
    print(get_url([
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
    ]))
