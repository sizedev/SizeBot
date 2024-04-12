import logging
from sizebot.lib.errors import InvalidStat, InvalidStatTag
from sizebot.lib.stats import statmap, taglist

re_full_string = r"\$(\w+=[^;$]+;?)+"
re_component = r"(\w+)=([^;$]+);?"

logger = logging.getLogger("sizebot")


class StatProxy:
    def __init__(self, name: str, tag: bool):
        self.name = name
        self.tag = tag

    def __repr__(self):
        return f"<StatProxy {'#' if self.tag else ''}{self.name}>"

    def __str__(self):
        return self.__repr__()
    
    @classmethod
    def parse(cls, s: str):
        logger.info(f"{s}: checking StatProxy...")
        tag = False
        if s.startswith("#"):
            logger.info("Looks like a tag.")
            tag = True
            s = s.removeprefix("#")

        if tag:
            if s not in taglist:
                logger.info(f"Looks like {s} isn't a tag.")
                logger.info(f"It's not in this list: {taglist}")
                raise InvalidStatTag(s)
            logger.info("Check passed!")
            return StatProxy(s, True)
        else:
            if s not in statmap.keys():
                logger.info(f"Looks like {s} isn't a stat.")
                logger.info(f"It's not in this list: {statmap.keys()}")
                raise InvalidStat(s)
            logger.info("Check passed!")
            return StatProxy(statmap[s], False)

    @classmethod
    async def convert(cls, ctx, argument):
        return cls.parse(argument)
