import logging
import random
from copy import copy
from typing import List
from sizeroyale.lib.embedtemplate import EmbedTemplate

import petname

from sizebot.lib.loglevels import ROYALE
from sizeroyale.lib.classes.royale import Royale
from sizeroyale.lib.errors import OutOfEventsError, OutOfPlayersError, ThisShouldNeverHappenException
from sizeroyale.lib.img_utils import merge_images

logger = logging.getLogger("sizebot")


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

    @property
    def round_title(self):
        if self.current_event_type == "bloodbath":
            event_type = "Cornucopia"
        else:
            event_type = self.current_event_type.capitalize()

        title = f"Day {self.current_day}: {event_type}"
        if self.current_arena:
            title += f" [{self.current_arena.name}]"

        return title

    @property
    def stats_screen(self):
        return EmbedTemplate(title = f"Size Royale Stats ({self.round_title})",
                             image = self.royale.stats_screen)

    @property
    def game_over_embed(self):
        if self.game_over == 0:
            return {"text": "GAME OVER! There are no winners."}
        if self.royale.teamwin:
            return {
                "text": f"GAME OVER! Winning Team: {self.game_over[0]}",
                "image": self.game_over[1]
            }
        return {
            "text": f"GAME OVER! Winning Player: {self.game_over[0].name}",
            "image": self.game_over[1]
        }

    def next(self) -> List[EmbedTemplate]:
        if self.game_over:
            logger.log(ROYALE, "This game is already completed. Please start a new game.")
            return [EmbedTemplate(title = "Size Royale",
                                  description = "This game is already completed. Please start a new game.")]
        if self.cannon_time:
            unreported_deaths = self.unreported_deaths
            self.unreported_deaths = []
            logger.log(ROYALE, f"[GAME] {len(unreported_deaths)} cannon shots sound through the arena.")
            return [EmbedTemplate(title = self.round_title,
                                  description = f"{len(unreported_deaths)} cannon shot{'' if len(unreported_deaths) == 1 else 's'} sound through the arena.",
                                  image = merge_images([p.image for p in unreported_deaths]))]
        round = self._next_round()
        if round is None:
            return None
        events = [EmbedTemplate(title = self.round_title,
                                description = event['text'],
                                image = event['image']) for event in round]
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
                logger.log(ROYALE, f"[GAME] GAME OVER! Winner: {self.royale.game_over}")
                return [self.game_over_embed]
            es = self._next_event(playerpool)
            for e in es:
                for p in e["players"]:
                    playerpool.pop(p)
                for d in e["deaths"]:
                    self.unreported_deaths.append(d)
                events.append(e)
        if self.running_arena:
            self.running_arena = False
            logger.log(ROYALE, "[ARENA] Arena over!")
            events.append({"text": "The arena is over."})

        return events

    def _next_event(self, playerpool: dict):
        if self.royale.game_over is not None:
            return [self.game_over_embed]
        if self.current_event_type in ["bloodbath", "feast", "arena"]:
            event_type = self.current_event_type
        elif self.current_event_type in ["day", "night"]:
            if self.random.randint(1, self.royale.deathrate) == 1:
                event_type = "fatal" + self.current_event_type
            else:
                event_type = self.current_event_type
        else:
            raise ThisShouldNeverHappenException("Round type not valid.")

        events = []

        if self.current_event_type == "arena":
            if not self.current_arena:
                self.current_arena = self.random.choice(self.royale.arenas)
                self.running_arena = True
                logger.log(ROYALE, f"[ARENA] Running arena {self.current_arena.name}...")
                events.append({"text": self.current_arena.description})
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
                    events.append(r)
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
                    events.append(r)
                except OutOfPlayersError:
                    events.remove(event)

        return events

    def __str__(self):
        return f"Game(seed={self.seed!r}\n{str(self.royale)}\n)"

    def __repr__(self):
        return f"Game(seed={self.seed}, royale={self.royale!r})"
