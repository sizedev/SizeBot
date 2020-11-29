import logging
import random
from copy import copy
from sizeroyale.lib.img_utils import merge_images
from sizeroyale.lib.loglevels import ROYALE

import petname

from sizeroyale.lib.classes.royale import Royale
from sizeroyale.lib.errors import OutOfEventsError, OutOfPlayersError, ThisShouldNeverHappenException

logger = logging.getLogger("sizeroyale")


class Game:
    def __init__(self, filepath, *, seed = None):
        self.royale = Royale(filepath, self)
        if self.royale.parser.errors:
            for e in self.royale.parser.errors:
                logger.error(e)

        if seed is None:
            self.seed = petname.generate(3, letters = 10)
        else:
            self.seed = seed

        self.random = random.Random()

        self.random.seed(self.seed)

        self.current_day = 0
        self.current_event_type = None
        self.current_arena = None
        self.running_arena = False
        self.feasted = False
        self.unreported_deaths = []

    @property
    def cannon_time(self):
        return self.unreported_deaths != []

    @property
    def game_over(self):
        return self.royale.game_over

    def next(self):
        if self.game_over:
            logger.log(ROYALE, "This game is already completed. Please start a new game.")
            return ("This game is already completed. Please start a new game.", None)
        if self.cannon_time:
            unreported_deaths = self.unreported_deaths
            self.unreported_deaths = []
            logger.log(ROYALE, f"[GAME] {len(unreported_deaths)} cannon shots sound through the arena.")
            return (f"{len(unreported_deaths)} cannon shot{'' if len(unreported_deaths) == 1 else 's'} sound through the arena.",
                    merge_images([p.image for p in unreported_deaths]))
        round = self._next_round()
        if round is None:
            return None
        events = []
        for e in round:
            events.append((e["text"], e["image"]))
        return events

    def _next_round(self):
        # Reset player pool.
        playerpool = self.royale.alive_players

        # Progress the round type forward.
        if self.current_day == 0:
            self.current_event_type = "bloodbath"
            self.current_day += 1

        # Switch to a normal day after the bloodbath.
        elif self.current_event_type == "bloodbath":
            self.current_event_type = "day"
        else:
            # Run a feast when half the population is eliminated.
            if self.royale.original_player_count / 2 > self.royale.remaining and self.feasted is False:
                self.current_event_type = "feast"
                self.feasted = True

            # Run an arena every 10.
            elif self.random.randint(1, self.royale.arenafreq) == 1:
                self.current_event_type = "arena"

            # Day -> night.
            elif self.current_event_type == "day":
                self.current_event_type = "night"

            # Rollover to day.
            elif (self.current_event_type == "night"
                  or self.current_event_type == "arena"
                  or self.current_event_type == "feast"):
                self.current_event_type = "day"
                self.current_day += 1

            else:
                raise ThisShouldNeverHappenException("Round type not valid.")

        logger.log(ROYALE, "[ROUND] " + self.current_event_type.capitalize() + f", Day {self.current_day}")
        events = []
        while playerpool:
            if self.game_over:
                logger.log(ROYALE, f"[GAME] GAME OVER! Winning Team: {self.royale.game_over}")
                return None
            e = self._next_event(playerpool)
            for p in e["players"]:
                playerpool.pop(p)
            for d in e["deaths"]:
                self.unreported_deaths.append(d)
            events.append(e)
        if self.running_arena:
            self.running_arena = False
            logger.log(ROYALE, "[ARENA] Arena over!")

        return events

    def _next_event(self, playerpool: dict):
        if self.royale.game_over is not None:
            logger.log(ROYALE, f"[GAME] GAME OVER! Winning Team: {self.royale.game_over}")
            return
        if self.current_event_type in ["bloodbath", "feast", "arena"]:
            event_type = self.current_event_type
        elif self.current_event_type in ["day", "night"]:
            if self.random.randint(1, self.royale.deathrate) == 1:
                event_type = "fatal" + self.current_event_type
            else:
                event_type = self.current_event_type
        else:
            raise ThisShouldNeverHappenException("Round type not valid.")

        if self.current_event_type == "arena":
            if not self.current_arena:
                self.current_arena = self.random.choice(self.royale.arenas)
                self.running_arena = True
                logger.log(ROYALE, f"[ARENA] Running arena {self.current_arena.name}...")
            trying_events = True
            events = copy(self.current_arena.events)
            while trying_events:
                if not events:
                    raise OutOfEventsError
                event = self.random.choices(events, [e.rarity for e in events])[0]
                try:
                    players = event.get_players(playerpool)
                    r = self.royale._run_event(event, players)
                    trying_events = False
                    return r
                except OutOfPlayersError:
                    events.remove(event)

        else:
            trying_events = True
            events = copy(getattr(self.royale.events, event_type + "_events"))
            while trying_events:
                if not events:
                    raise OutOfEventsError
                event = self.random.choices(events, [e.rarity for e in events])[0]
                try:
                    players = event.get_players(playerpool)
                    r = self.royale._run_event(event, players)
                    trying_events = False
                    return r
                except OutOfPlayersError:
                    events.remove(event)

    def __str__(self):
        return f"Game(seed={self.seed!r}\n{str(self.royale)}\n)"

    def __repr__(self):
        return f"Game(seed={self.seed}, royale={self.royale!r})"
