import importlib.resources as pkg_resources
import csv
import sizebot.data
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV
from sizebot.lib.userdb import User


def get_facts(size: SV, prefix: str = "You are") -> list[str]:
    facts_csv = pkg_resources.read_text(sizebot.data, "gifts.txt").splitlines()
    csv_reader = csv.reader(facts_csv)

    facts = []

    for n, line in enumerate(csv_reader):
        if n == 0:
            continue

        minimum = SV(line[0]) if line[0] else SV(0)
        maximum = SV(line[1]) if line[1] else SV(SV.infinity)
        fact = line[2]

        if minimum < size <= maximum:
            facts.append(prefix + " " + fact + ".")

    return facts


def get_facts_from_user(userdata: User, prefix: str = "You are") -> list[str]:
    statbox = StatBox.load(userdata.stats).scale(userdata.scale)
    height = statbox.stats_by_key['height'].value
    return get_facts(height, prefix)
