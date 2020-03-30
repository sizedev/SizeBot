import asyncio

import inflect

from sizebot.lib import objs

inflecter = inflect.engine()

loop2 = asyncio.get_event_loop()
loop2.run_until_complete(objs.init())
loop2.close()


def test_plural_matching():
    for o in objs.objects:
        assert (inflecter.plural(o.name) == o.namePlural) is True
