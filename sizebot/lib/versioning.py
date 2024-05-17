from collections.abc import Callable

from packaging import version

import sizebot
from sizebot.conf import conf


def is_released(v: str) -> bool:
    if v is None:
        return False
    if conf.environment == "development":
        try:
            bot_v = sizebot.__dev_version__
        except AttributeError:
            return True
    else:
        bot_v = sizebot.__version__
    return version.parse(bot_v) >= version.parse(v)


def release_on(release_version: str) -> Callable:
    def wrapper(fn: Callable) -> Callable | None:
        active = is_released(release_version)
        if not active:
            return None
        return fn
    return wrapper
