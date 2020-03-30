import asyncio

import inflect

from sizebot.lib import objs

inflecter = inflect.engine()

asyncio.run(objs.init())


def test_plural_matching():
    for o in objs.objects:
        assert (inflecter.plural(o.name) == o.namePlural) is True
