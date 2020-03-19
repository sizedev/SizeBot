# The "edge" extensions allows bot admins (and later guild owners [SB4]) to set a largest/smallest user (for their server [SB4]).
# It does this by sseeing if they are the largest or smallest user (in the guild [SB4]), and if they aren't setting their height
# to either 1.1x or 0.9x of the largest or smallest user (in the guild [SB4]), respectively.

import toml
from sizebot import conf

try:
    with open(conf.edgepath, "r") as f:
        edgedict = toml.loads(f.read())
except (FileNotFoundError, TypeError, toml.TomlDecodeError):
    edgedict = {"edges": {"smallest": None, "largest": None}}
    with open(conf.edgepath, "w") as f:
        f.write(toml.dump(edgedict))


async def on_message(m):
    pass
