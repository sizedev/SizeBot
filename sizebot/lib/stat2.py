import numexpr

class Equation:
    VARIABLES = ["x", "y", "z", "a", "b", "c"]

    def __init__(self, expression: str, attrs: list[str]):
        self.expression = expression
        self.attrs = attrs

    def calculate(self, stats: "Stats"):
        for a in self.attrs:
            try:
                getattr(stats, a)
            except Exception as e:
                raise e
        ld = {self.VARIABLES[n]: getattr(stats, a) for n, a in enumerate(self.attrs)}
        return numexpr.evaluate(self.expression, ld, {})

class Stat:
    def __init__(self):
        self.equation = Equation()