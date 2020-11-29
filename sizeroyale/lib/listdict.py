import itertools
from typing import TypeVar, Generic

A = TypeVar('A')
B = TypeVar('B')


class ListDict(dict, Generic[A, B]):
    def getByIndex(self, n: int):
        return next(itertools.islice(self.values(), n, None))
