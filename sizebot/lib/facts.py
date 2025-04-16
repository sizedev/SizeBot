import importlib.resources as pkg_resources
import csv
import logging
import sizebot.data
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV, Decimal
from sizebot.lib.userdb import User

logger = logging.getLogger("sizebot")

def get_facts(size: SV, prefix: str = "You are", wiggle: float = 10) -> list[str]:
    facts_csv = pkg_resources.read_text(sizebot.data, "facts.csv").splitlines()
    csv_reader = csv.reader(facts_csv)

    facts = []

    for n, line in enumerate(csv_reader):
        if n == 0:
            continue

        minimum = SV(line[0]) if line[0] else None
        maximum = SV(line[1]) if line[1] else None
        if not minimum:
            minimum = maximum / Decimal(wiggle)
        if not maximum:
            maximum = minimum * Decimal(wiggle)

        fact = line[2]

        if minimum < size <= maximum:
            facts.append(prefix + " " + fact + ".")

    if not facts:
        return [f"{prefix} outside of the bound of facts."]

    return facts


def get_facts_from_user(userdata: User, prefix: str = "You are", wiggle: float = 10) -> list[str]:
    statbox = StatBox.load(userdata.stats).scale(userdata.scale)
    height = statbox.stats_by_key['height'].value
    return get_facts(height, prefix, wiggle)
