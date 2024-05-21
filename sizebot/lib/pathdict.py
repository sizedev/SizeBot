from typing import Any

import re

RE_COMPONENT = re.compile(r'\[\d+\]|[^\[\].]+')
RE_INDEX = re.compile(r'\[(\d+)\]')
RE_KEY = re.compile(r'[^\[\].]+')
RE_RESERVED = re.compile(r'[\[\]\.]')


class BadPathException(Exception):
    pass


def _parse_component(component: str) -> int | str:
    index_match = RE_INDEX.match(component)
    if index_match:
        return int(index_match[1])
    elif RE_KEY.match(component):
        return component
    else:
        raise BadPathException


def _build_path(components: list[int | str]) -> str:
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


def _parse_path(path: str) -> list[int | str]:
    components = [_parse_component(c) for c in RE_COMPONENT.findall(path)]
    if path != _build_path(components):
        raise BadPathException
    return components


class PathDict:
    def __init__(self, data: Any = {}):
        self._values = data

    def __getitem__(self, path: str) -> Any:
        """value = PathDict[path]"""
        branch = self._values
        try:
            components = _parse_path(path)
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
        components = _parse_path(path)
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

    def __str__(self) -> str:
        return str(self._values)

    def __repr__(self) -> str:
        return repr(self._values)


SENTINEL = object()


def get_by_path(data: dict, path: str, default: Any = SENTINEL) -> Any:
    if default is SENTINEL:
        return PathDict(data)[path]
    else:
        return PathDict(data).get(path, default)


def set_by_path(data: dict, path: str, value: Any):
    PathDict(data)[path] = value
