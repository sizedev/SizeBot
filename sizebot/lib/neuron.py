from typing import Literal, get_args

from discord import Embed
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV
from sizebot.lib.userdb import User
from sizebot.lib.utils import pretty_time_delta


NEURON_SPEED = SV(95)
Part = Literal["arm", "hand", "leg", "foot"]


def get_speed_to_part(statbox: StatBox, part: Part) -> Decimal:
    match part:
        case "arm":
            length: SV = statbox.stats_by_key["height"].value - statbox.stats_by_key["shoulderheight"].value
        case "hand":
            length: SV = statbox.stats_by_key["height"].value - statbox.stats_by_key["shoulderheight"].value + statbox.stats_by_key["armlegnth"].value
        case "leg":
            length: SV = statbox.stats_by_key["height"].value - statbox.stats_by_key["waistheight"].value
        case "foot":
            length: SV = statbox.stats_by_key["height"].value

    return Decimal(length / NEURON_SPEED)


def get_neuron_embed(userdata: User) -> Embed:
    statbox = StatBox.load(userdata.stats).scale(userdata.scale)
    e = Embed(title = f"Neuron Travel Distance for {statbox.stats_by_key['nickname'].value}",
              description = f"{statbox.stats_by_key['nickname'].value} is {statbox.stats_by_key['height'].value:.1mu} tall.")
    for part in get_args(Part):
        e.add_field(name = part.title(), value = pretty_time_delta(get_speed_to_part(statbox, part)))

    return e
