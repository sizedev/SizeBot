import logging
import random
from copy import copy
from sizeroyale.lib.runnableevent import RunnableEvent
from typing import List
from sizeroyale.lib.embedtemplate import EmbedTemplate

import petname

from sizebot.lib.loglevels import ROYALE
from sizeroyale.lib.classes.royale import Royale
from sizeroyale.lib.errors import OutOfEventsError, OutOfPlayersError, ThisShouldNeverHappenException
from sizeroyale.lib.img_utils import merge_images

logger = logging.getLogger("sizebot")


class Game:
    def __init__(self, *, seed = None):
        if seed is None:
            self.seed = petname.generate(3, letters = 10)
        else:
            self.seed = seed

        self.random = random.Random()

        self.random.seed(self.seed)

        self.data = None
        self.rounds = 0

        self.royale = None
        self.current_day = 0
        self.current_event_type = None
        self.current_arena = None
        self.running_arena = False
        self.feasted = False
        self.unreported_deaths = []

    async def load(self, data):
        self.royale = Royale(self)
        return self.royale.load(data)

        # if self.royale.parser.errors:
        #     return self.royale.parser.errors

    @property
    def cannon_time(self):
        return self.unreported_deaths != []

    async def game_over(self):
        return await self.royale.game_over()

    @property
    def round_title(self):
        if self.current_event_type == "bloodbath":
            event_type = "Cornucopia"
        elif self.current_event_type is None:
            event_type = "[UNINITIALIZED]"
        else:
            event_type = self.current_event_type.capitalize()

        title = f"Day {self.current_day}: {event_type}"
        if self.current_arena:
            title += f" [{self.current_arena.name}]"

        return title

    async def stats_screen(self):
        return EmbedTemplate(title = f"Size Royale Stats ({self.round_title})",
                             image = await self.royale.stats_screen())

    async def game_over_embed(self):
        g_o = await self.game_over()
        if g_o == 0:
            return RunnableEvent(text = "GAME OVER! There are no winners.")
        if self.royale.teamwin:
            return RunnableEvent(
                text = f"GAME OVER! Winning Team: {g_o[0]}",
                image = g_o[1]
            )
        return RunnableEvent(
            text = f"GAME OVER! Winning Player: {g_o[0].name}",
            image = g_o[1]
        )

    async def next(self) -> List[EmbedTemplate]:
        self.rounds += 1
        if await self.game_over():
            logger.log(ROYALE, "This game is already completed. Please start a new game.")
            return [EmbedTemplate(title = "Size Royale",
                                  description = "This game is already completed. Please start a new game.")]
        if self.cannon_time:
            unreported_deaths = self.unreported_deaths
            self.unreported_deaths = []
            logger.log(ROYALE, f"[GAME] {len(unreported_deaths)} cannon shots sound through the arena.")
            return [EmbedTemplate(title = f"Day {self.current_day}: Those Who Fell",
                                  description = f"{len(unreported_deaths)} cannon shot{'' if len(unreported_deaths) == 1 else 's'} sound through the arena.",
                                  image = merge_images([await p.get_image() for p in unreported_deaths]))]
        round = await self._next_round()
        if round is None:
            return None
        events = [EmbedTemplate(title = self.round_title,
                                description = event.text,
                                image = event.image) for event in round]
        return events

    async def _next_round(self):
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
            if await self.game_over():
                logger.log(ROYALE, f"[GAME] GAME OVER! Winner: {await self.royale.game_over()}")
                return [await self.game_over_embed()]
            es = await self._next_event(playerpool)
            for e in es:
                for p in e.players:
                    playerpool.pop(p)
                for d in e.deaths:
                    self.unreported_deaths.append(d)
                events.append(e)
        if self.running_arena:
            self.running_arena = False
            self.current_arena = None
            logger.log(ROYALE, "[ARENA] Arena over!")
            events.append(RunnableEvent(text = "The arena is over."))

        return events

    async def _next_event(self, playerpool: dict):
        if await self.royale.game_over() is not None:
            return [await self.game_over_embed()]
        if self.current_event_type in ["bloodbath", "feast", "arena"]:
            event_type = self.current_event_type
        elif self.current_event_type in ["day", "night"]:
            if self.random.randint(1, self.royale.deathrate) == 1:
                event_type = "fatal" + self.current_event_type
            else:
                event_type = self.current_event_type
        else:
            raise ThisShouldNeverHappenException("Round type not valid.")

        es = []

        if self.current_event_type == "arena":
            if not self.current_arena:
                self.current_arena = self.random.choice(self.royale.arenas)
                self.running_arena = True
                logger.log(ROYALE, f"[ARENA] Running arena {self.current_arena.name}...")
                es.append(RunnableEvent(text = self.current_arena.description))
            trying_events = True
            events = copy(self.current_arena.events)
            while trying_events:
                if not events:
                    raise OutOfEventsError(f"arena {self.current_arena.name}")
                event = self.random.choices(events, [e.rarity for e in events])[0]
                try:
                    players = event.get_players(playerpool)
                    r = await self.royale._run_event(event, players)
                    trying_events = False
                    es.append(r)
                except OutOfPlayersError:
                    events.remove(event)

        else:
            trying_events = True
            events = copy(getattr(self.royale.events, event_type + "_events"))
            while trying_events:
                if not events:
                    raise OutOfEventsError(self.round_title)
                event = self.random.choices(events, [e.rarity for e in events])[0]
                try:
                    players = event.get_players(playerpool)
                    r = await self.royale._run_event(event, players)
                    trying_events = False
                    es.append(r)
                except OutOfPlayersError:
                    events.remove(event)

        return es

    def toJSON(self):
        return {
            "data": self.data,
            "seed": self.seed,
            "rounds": self.rounds
        }

    @classmethod
    async def fromJSON(cls, jsondata):
        game = cls(seed = jsondata["seed"])
        await game.load(jsondata["data"])
        for i in range(jsondata["rounds"]):
            await game.next()
        return game

    def __str__(self):
        return f"Game(seed={self.seed!r}\n{str(self.royale)}\n)"

    def __repr__(self):
        return f"Game(seed={self.seed}, royale={self.royale!r})"
