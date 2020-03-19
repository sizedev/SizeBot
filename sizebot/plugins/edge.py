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
