import importlib.resources as pkg_resources
import csv
import logging
import sizebot.data
from sizebot.lib.stats import StatBox
from sizebot.lib.units import SV, Decimal
from sizebot.lib.userdb import User

logger = logging.getLogger("sizebot")

def get_facts(size: SV, prefix: str = "You are", wiggle: float = 10) -> list[str]:
    wiggle = Decimal(wiggle)
    facts_csv = pkg_resources.read_text(sizebot.data, "facts.csv").splitlines()
    csv_reader = csv.reader(facts_csv)

    true_facts = []
    close_facts = []

    for n, line in enumerate(csv_reader):
        if n == 0:
            continue

        minimum = SV(line[0]) if line[0] else None
        maximum = SV(line[1]) if line[1] else None

        # This assumes that atleast one bound is set.
        soft_minimum = minimum if minimum is not None else maximum / wiggle
        soft_maximum = maximum if maximum is not None else minimum * wiggle

        fact = line[2]

        if minimum is None or maximum is None:
            # Check if unbounded fact is closely true, or generally true
            if soft_minimum < size <= soft_maximum:
                close_facts.append(f"{prefix} {fact}.")
            elif (minimum or SV(0)) < size <= (maximum or SV(SV.infinity)):
                true_facts.append(f"{prefix} {fact}.")
            continue
        
        # Check if a bounded fact is true and consider it 'close'
        if minimum < size <= maximum:
            close_facts.append(f"{prefix} {fact}.")

    if not close_facts:
        if not true_facts:
            return [f"{prefix} outside of the bounds of all facts."]
        return [f'{prefix} outside the bounds of relevant facts.']

    return close_facts


def get_facts_from_user(userdata: User, prefix: str = "You are", wiggle: float = 10) -> list[str]:
    statbox = StatBox.load(userdata.stats).scale(userdata.scale)
    height = statbox.stats_by_key['height'].value
    return get_facts(height, prefix, wiggle)
