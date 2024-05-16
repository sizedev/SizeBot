from collections.abc import Callable

import functools

import arrow


timedfuncs: list[Callable] = []


def timethis(name: str):
    def wrapper(fn: Callable):
        fn.name = name

        @functools.wraps
        def wrapped(*args, **kwargs):
            fn.start = arrow.now()
            res = fn(args, **kwargs)
            fn.end = arrow.now()
            return res
        timedfuncs.append(wrapped)
        return wrapped
    return wrapper


for fn in timedfuncs:
    print(fn.name, fn.end - fn.start)
