import asyncio
import io
import re

from tqdm import trange

from sizeroyale.lib.errors import ParseError
from sizeroyale.lib.classes.arena import Arena
from sizeroyale.lib.classes.event import Event
from sizeroyale.lib.classes.player import Player
from sizeroyale.lib.classes.setup import Setup

re_header = r"\[(.*)\]"
re_quotes = r"\"(.*)\""
re_arena = r"\<(.*)\>\s*\"(.*)\""
re_digit = r"\d"


class Parser:
    def __init__(self, game, data: str):
        self._game = game
        self._lines = data.splitlines()
        self.original_line_numbers = {}
        self.errors = []

        self.minsize = None
        self.maxsize = None
        self.autoelim = None
        self.teamwin = None
        self.deathrate = None
        self.players = {}
        self.arenas = []
        self.bloodbath_events = []
        self.day_events = []
        self.night_events = []
        self.fatalday_events = []
        self.fatalnight_events = []
        self.feast_events = []

        self._current_header = None
        self._current_arena = None
        self._current_line = None
        self._skip_next_line = False

        # Setup
        self._clean_lines()

    async def parse(self):
        pbar = io.StringIO()
        if not self.lines:
            raise ParseError("No lines to parse!")
        for n in trange(len(self.lines), desc="Parsing...", file = pbar, ascii = False, ncols = 100):
            try:
                await self._parse_line(n)
            except ParseError as e:
                self.errors.append(f"Line {self.original_line_numbers[n]}: " + e.message)
            yield pbar.getvalue()
            pbar.seek(0)
            pbar.truncate()
            await asyncio.sleep(0.025)
        # If there is still a arena in the queue, add it.
        if self.arenas is not None:
            self.arenas.append(self._current_arena)
        self._current_arena = None

    def _clean_lines(self):
        fixed_lines = []
        cln = 0

        for line in self._lines:
            # No newlines, please.
            cln += 1
            new_line = line.strip()
            new_line = new_line.replace("\n", "")
            # F*** smart quotes.
            new_line = new_line.replace("“", "\"")
            new_line = new_line.replace("”", "\"")
            # Don't bother adding back blank lines.
            if new_line != "":
                fixed_lines.append(new_line)
                self.original_line_numbers[len(fixed_lines) - 1] = cln

        self.lines = fixed_lines

    def _read_line(self, n: int):
        return self.lines[n]

    @property
    def _read_next_line(self):
        self._skip_next_line = True
        return self._read_line(self._current_line + 1)

    async def _parse_line(self, n: int):
        self._current_line = n
        line = self.lines[n]

        # Skip
        if self._skip_next_line:
            self._skip_next_line = False
            return

        # Comments
        if line.startswith("#"):
            return

        # Headers
        if (match := re.match(re_header, line)):
            header = match.group(1)
            self._current_header = header
            return

        # Setup
        if self._current_header == "setup":
            setup = Setup(line)
            self.autoelim = setup.autoelim
            self.teamwin = setup.teamwin
            self.deathrate = setup.deathrate
            self.maxsize = setup.maxsize
            self.minsize = setup.minsize
            self.arenafreq = setup.arenafreq
            self.unitsystem = setup.unitsystem
            return

        # Players
        elif self._current_header == "players":
            if (match := re.match(re_quotes, line)):
                name = match.group(1)
            else:
                raise ParseError("No quoted string found for a player!")
            meta = self._read_next_line

            player = Player(self._game, name, meta)
            self.players[player.name] = player

        # Events
        elif self._current_header in ["bloodbath", "day", "night", "fatalday", "fatalnight", "feast"]:
            if (match := re.match(re_quotes, line)):
                event_text = match.group(1)
            else:
                raise ParseError("No quoted string found for event!")
            meta = self._read_next_line

            event = Event(self._game, event_text, meta)
            getattr(self, self._current_header + "_events").append(event)

        # Arenas
        elif self._current_header == "arena":
            if (match := re.match(re_arena, line)):
                if self._current_arena:
                    self.arenas.append(self._current_arena)
                    self._current_arena = None
                arena_name = match.group(1)
                arena_description = match.group(2)
                self._current_arena = Arena(arena_name, arena_description)
            elif (match := re.match(re_quotes, line)):
                if (match := re.match(re_quotes, line)):
                    event_text = match.group(1)
                else:
                    raise ParseError("No quoted string found for event!")
                meta = self._read_next_line

                event = Event(self._game, event_text, meta)
                self._current_arena.add_event(event)

        else:
            return
