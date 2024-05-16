from typing import TypeVar

T = TypeVar("T")


class AttrDict[T]:
    __slots__ = ["_values"]

    def __init__(self, data: dict[str, T] = {}):
        # This avoids an infinite recursion issue with __getattr__()
        super().__setattr__("_values", data)

    def __getattr__(self, key: str) -> T:
        """value = attrdict.key"""
        try:
            return self._values[key]
        except KeyError:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {key!r}")

    def __setattr__(self, key: str, value: T):
        """attrdict.key = value"""
        if key in self.__slots__:
            raise AttributeError(f"{key!r} is a reserved attribute for {self.__class__.__name__!r}")
        self._values[key] = value

    def __getitem__(self, key: str) -> T:
        """value = attrdict[key]"""
        return self._values[key]

    def __setitem__(self, key: str, value: T):
        """attrdict[key] = value"""
        if key in self.__slots__:
            raise KeyError(f"{key!r} is a reserved key for {self.__class__.__name__!r}")
        self._values[key] = value
