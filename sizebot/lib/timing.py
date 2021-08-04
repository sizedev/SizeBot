import functools

import arrow


timedfuncs = []


def timethis(name):
    def wrapper(fn):
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


@timethis("digipee")
def on_message(m):
    m.reply("digipee")
