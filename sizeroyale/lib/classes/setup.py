from sizeroyale.lib.classes.metaparser import MetaParser


class Setup:
    valid_data = [("autoelim", "single"), ("deathrate", "single"), ("teamwin", "single"),
                  ("maxsize", "single"), ("minsize", "single"), ("arenafreq", "single"),
                  ("unitsystem", "single")]

    def __init__(self, meta):
        self._original_metadata = meta
        self._metadata = MetaParser(type(self)).parse(meta)
        self.autoelim = self._metadata.autoelim
        self.teamwin = self._metadata.teamwin
        self.deathrate = self._metadata.deathrate
        self.maxsize = self._metadata.maxsize
        self.minsize = self._metadata.minsize
        self.arenafreq = self._metadata.arenafreq
        self.unitsystem = self._metadata.unitsystem

    def __str__(self):
        return str(self)

    def __repr__(self):
        return f"Setup(autoelim={self.autoelim!r}, deathrate={self.deathrate!r}, teamwin={self.teamwin!r}\
                 maxsize={self.maxsize!r}, minsize={self.maxsize!r}, arenafreq={self.arenafreq!r}, \
                 unitsystem={self.unitsystem!r})"
