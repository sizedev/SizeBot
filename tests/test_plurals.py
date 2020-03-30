import asyncio

from sizebot.lib import objs, language

inflecter = language.engine

language.load()
asyncio.run(objs.init())


def test_plural_matching():
    failures = [(o.name, o.namePlural, inflecter.plural_noun(o.name)) for o in objs.objects if inflecter.plural_noun(o.name) != o.namePlural]
    assert failures == []
