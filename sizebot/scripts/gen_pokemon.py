import requests
import json

colormap = {
    "black": 0x000000,
    "blue": 0x0000ff,
    "brown": 0x331100,
    "gray": 0x777777,
    "green": 0x00ff00,
    "pink": 0xff00ff,
    "purple": 0x770077,
    "red": 0xff0000,
    "white": 0xffffff,
    "yellow": 0xffff00
}

offset = 1
POKE_URL = "https://pokeapi.co/api/v2/"
ALL_POKEMON = POKE_URL + f"pokemon-species?offset={offset - 1}&limit={898 - offset}"

data = []

pokemon_menu: list[dict[str, str]] = requests.get(ALL_POKEMON).json()['results']

nd = offset
for pokemon in pokemon_menu:
    name: str = pokemon['name'].replace('-', ' ').title()  # data
    natdex: int = nd  # data
    generation_id: int = None
    region: str = None
    types: list[str] = []
    height: float = None
    weight: float = None
    color: int = None
    flavor: str = None
    sprite: str = None

    def add_to_data():
        data.append(
            {
                "name": name,
                "natdex": natdex,
                "generation": generation_id,
                "region": region,
                "types": types,
                "height": height,
                "weight": weight,
                "color": color,
                "flavor_text": flavor,
                "sprite": sprite
            }
        )
        color_string = f"#{color:06X}" if color is not None else "???"
        print(f"\n{name} #{natdex} (Generation {generation_id}: {region})\n"
              f"Type(s): {types} | Height: {height}m | Weight: {weight}g | Color: {color_string}\n"
              f"{flavor}\n")

    # -----------------------------------

    print(f"Loading {name} #{natdex}...")
    nd += 1

    try:
        pokemon = requests.get(POKE_URL + f"/pokemon/{natdex}").json()
        for t in pokemon['types']:
            types.append(t['type']['name'])
        height = pokemon['height'] / 10
        weight = pokemon['weight'] * 100
        sprite = pokemon['sprites']['front_default']
    except Exception:
        print("Couldn't load pokemon.")
        continue  # Really no point...

    try:
        species = requests.get(pokemon['species']['url']).json()
        colorname = species['color']['name']
        color = colormap[colorname]
        for f in species['flavor_text_entries']:
            if f['language']['name'] == "en":
                flavor = f['flavor_text'].replace("\n", " ").replace("\f", " ")
                break
    except Exception:
        print("Couldn't load species.")

    try:
        generation = requests.get(species['generation']['url']).json()
        generation_id = generation['id']
        region = generation['main_region']['name'].title()
    except Exception:
        print("Couldn't load generation.")

    add_to_data()


with open("./pokemon.json", "w+") as f:
    json.dump(data, f)
