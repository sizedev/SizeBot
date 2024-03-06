import json
import requests
from typing import Any, Literal

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.errors import ThisShouldNeverHappenException
from sizebot.lib.units import WV

OZ_TO_G = Decimal("28.3495")

GOLD_URL = R"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
SILVER_URL = R"https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
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
    if r.status != 200:
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

    PRICE_PER_OZ = j[0]["spreadProfilePrices"][0]["ask"]
    PRICE_PER_G = PRICE_PER_OZ * OZ_TO_G

    return weight * PRICE_PER_G
