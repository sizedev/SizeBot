class Arena:
    def __init__(self, name: str, description: str, *, events: list = []):
        self.name = name
        self.description = description
        self.events = events

    def add_event(self, e):
        self.events.append(e)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"Arena(name={self.name!r}, description={self.description!r}, events={self.events!r})"
