import itertools


class ListDict(dict):
    def getByIndex(self, n: int):
        return next(itertools.islice(self.values(), n, None))
