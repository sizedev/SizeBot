import json
from math import ceil
import requests
from typing import Any, Literal

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.errors import ThisShouldNeverHappenException
from sizebot.lib.units import WV

G_PER_OZ = Decimal("28.3495")

GOLD_URL = R"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
SILVER_URL = R"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAG/USD"
PLATINUM_URL = R"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XPT/USD"
PALLADIUM_URL = R"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XPD/USD"

Dollars = float
Metal = Literal["gold", "silver", "platinum", "palladium"]

def get_json_response(url: str) -> Any:
    r = requests.get(url)
    try:
        j = json.loads(r.text)
    except json.JSONDecodeError as e:
        raise e
    if r.status_code != 200:
        raise Exception(f"The API returned a code {r.status}.")
    return j

def metal_value(metal: Metal, weight: WV) -> Dollars:
    if metal == "gold":
        url = GOLD_URL
    elif metal == "palladium":
        url = PALLADIUM_URL
    elif metal == "platinum":
        url = PLATINUM_URL
    elif metal == "silver":
        url = SILVER_URL
    else:
        raise ThisShouldNeverHappenException(f"Metal type {metal} unrecognized.")
    
    j = get_json_response(url)

    PRICE_PER_OZ = Decimal(j[0]["spreadProfilePrices"][0]["ask"])
    PRICE_PER_G = PRICE_PER_OZ / G_PER_OZ

    return Decimal(weight) * PRICE_PER_G

def nugget_value(weight: WV) -> tuple[Dollars, int]:
    NUGGET_WEIGHT = 16
    prices = [(40, 13.49), (20, 7.49), (10, 6.39), (6, 3.99), (4, 2.49), (1, 0.50)]
    prices: list[tuple[int, float]] = [(p[0], p[1] / p[0]) for p in prices]

    nugget_count = weight / NUGGET_WEIGHT
    nc = nugget_count
    total = 0
    for count, price in prices:
        available_nuggets = (nc // count) * count
        total += available_nuggets * Decimal(price)
        nc -= available_nuggets
    if nc:
        total += (nc * Decimal(0.50))
    return total, ceil(nugget_count)
