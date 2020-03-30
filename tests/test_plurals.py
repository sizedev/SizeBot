from sizebot.lib import objs
import inflect

inflecter = inflect.engine()


async def test_plural_matching():
    await objs.init()

    for o in objs.objects:
        assert (inflecter.plural(o.name) == o.namePlural) is True
