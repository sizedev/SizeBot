import importlib.resources as pkg_resources
from typing import Literal

import pyinflect
import inflect
import toml

import sizebot.data

InflectionForm = Literal["VBD", "VBG"]

engine: inflect.engine = inflect.engine()


def _get_infection(word: str, form: InflectionForm) -> str | None:
    inf = pyinflect.getInflection(word, form)
    if inf is None:
        return None
    return inf[0]


def get_verb_present(verb: str) -> str | None:
    return _get_infection(verb, "VBG")


def get_verb_past(verb: str) -> str | None:
    return _get_infection(verb, "VBD")


def get_plural(noun: str) -> str:
    return engine.plural_noun(noun)


def get_indefinite_article(noun: str) -> str:
    return engine.a(noun)


def load():
    plurals: dict[str, dict[str, str]] = toml.loads(pkg_resources.read_text(sizebot.data, "plurals.ini"))
    for s, p in plurals["plurals"].items():
        engine.defnoun(s, p)
