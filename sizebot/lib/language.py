import inflect
import toml
import importlib.resources as pkg_resources

import sizebot.data

engine = None


def load():
    global engine
    engine = inflect.engine()
    plurals = toml.loads(pkg_resources.read_text(sizebot.data, "plurals.ini"))
    for s, p in plurals["plurals"].items():
        engine.defnoun(s, p)


def getPlural(noun):
    overrides = {}
    if noun in overrides:
        return overrides[noun]
    return engine.plural_noun(noun)


def getIndefiniteArticle(noun):
    return engine.a(noun)
