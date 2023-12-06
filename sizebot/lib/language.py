import importlib.resources as pkg_resources

import inflect
import toml

import sizebot.data

engine = None

ing = {
    "walk": "walking",
    "run": "running",
    "climb": "climbing",
    "crawl": "crawling",
    "swim": "swimming"
}

ed = {
    "walk": "walked",
    "run": "ran",
    "climb": "climbed",
    "crawl": "crawled",
    "swim": "swam"
}


def load():
    global engine
    engine = inflect.engine()
    plurals = toml.loads(pkg_resources.read_text(sizebot.data, "plurals.ini"))
    for s, p in plurals["plurals"].items():
        engine.defnoun(s, p)


def get_plural(noun):
    overrides = {}
    if noun in overrides:
        return overrides[noun]
    return engine.plural_noun(noun)


def get_indefinite_article(noun):
    return engine.a(noun)
