from typing import Type

from sizebot.lib.attrdict import AttrDict
from sizeroyale.lib.errors import ParseError


class MetaParser:
    """
    Parse a string of metadata based on a type.
    That type must define <type>.valid_data, a series of 2-tuples
    of type (str, str) where the first string is the name of the data,
    and the second is one of the following:
    single: allows only one of the that type of data to exist on an object.
    Will raise a ParseError if there's more than one of this type in the data.
    list: allows an abirtary amount of that type of data per object, and
    returns them as a list.
    compound: allows an abitrary amount of that type of data, and returns a
    list of tuples of an abitrary length, by splitting the value by colons.
    e.g.: "a:b:c" -> {a: (b, c)} | "a:b:c:d" -> {a: (b, c, d)}
    """
    def __init__(self, t: Type):
        self.t = t

    def parse(self, s: str) -> AttrDict:

        returndict = {}

        try:
            validdata = dict(self.t.valid_data)
        except AttributeError:
            raise ParseError(f"Type {self.t} does not define valid metadata.")

        items = s.split(",")
        for item in items:
            item = item.strip()
            kv = item.split(":", 1)
            try:
                k, v = (kv[0], kv[1])
            except IndexError:
                raise ParseError(f"Metatag {kv[0]} has no value.")
            if k in validdata:
                datatype = validdata[k]
                if datatype == "single":
                    if k in returndict:
                        raise ParseError(f"Metadata type {k} defined multiple times, but is a 'single' type data.")
                    else:
                        returndict[k] = v
                elif datatype == "list":
                    if k in returndict:
                        returndict[k].append(v)
                    else:
                        returndict[k] = [v]
                elif datatype == "compound":
                    split = tuple(v.split(":"))
                    if k in returndict:
                        returndict[k].append(split)
                    else:
                        returndict[k] = [split]
                else:
                    raise ParseError(f"Invalid data type {datatype}.")

        for d in validdata:
            if d not in returndict:
                returndict[d] = None

        return AttrDict(returndict)
