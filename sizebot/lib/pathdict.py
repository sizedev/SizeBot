from typing import Any

import re

RE_COMPONENT = re.compile(r'\[\d+\]|[^\[\].]+')
RE_INDEX = re.compile(r'\[(\d+)\]')
RE_KEY = re.compile(r'[^\[\].]+')
RE_RESERVED = re.compile(r'[\[\]\.]')


class BadPathException(Exception):
    pass


def parse_component(component: str) -> int | str:
    index_match = RE_INDEX.match(component)
    if index_match:
        return int(index_match[1])
    elif RE_KEY.match(component):
        return component
    else:
        raise BadPathException


# TODO: CamelCase
def buildPath(components: list[int | str]) -> str:
    path = ""
    for c in components:
        if isinstance(c, int):
            path += f"[{c}]"
        elif not RE_RESERVED.search(c):
            path += f".{c}"
        else:
            raise BadPathException
    if path.startswith("."):
        path = path[1:]
    return path


# TODO: CamelCase
def parsePath(path: str) -> list[int | str]:
    components = [parse_component(c) for c in RE_COMPONENT.findall(path)]
    if path != buildPath(components):
        raise BadPathException
    return components


class PathDict:
    def __init__(self, data={}):
        self._values = data

    def __getitem__(self, path: str) -> Any:
        """value = PathDict[path]"""
        branch = self._values
        try:
            components = parsePath(path)
        except BadPathException:
            raise BadPathException(f"Bad Path: {path}")

        for c in components:
            try:
                branch = branch[c]
            except (KeyError, IndexError):
                err = KeyError(f"Path not found: {path!r}")
                err.path = path
                raise err

        return branch

    def __setitem__(self, path: str, value: Any):
        """PathDict[path] = value"""
        branch = self._values
        components = parsePath(path)
        last = components.pop()

        for c in components:
            try:
                branch = branch[c]
            except (KeyError, IndexError):
                branch[c] = dict()
                branch = branch[c]
        branch[last] = value

    def get(self, path: str, default: Any = None) -> Any:
        """value = PathDict.get(path, default)"""
        try:
            return self[path]
        except KeyError:
            return default

    # TODO: CamelCase
    def toDict(self) -> dict[str, Any]:
        return self._values

    def __str__(self):
        return str(self._values)

    def __repr__(self):
        return repr(self._values)
