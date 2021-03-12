import logging
from sizebot.lib.diff import Diff
from sizebot.lib.utils import minmax
from sizeroyale.lib.runnableevent import RunnableEvent
from typing import Dict, Optional

from sizebot.lib.attrdict import AttrDict
from sizebot.lib.digidecimal import Decimal
from sizebot.lib.loglevels import ROYALE
from sizebot.lib.utils import randRangeLog
from sizebot.lib.units import SV
from sizeroyale.lib.classes.event import Event
from sizeroyale.lib.classes.parser import Parser
from sizeroyale.lib.classes.player import Player
from sizeroyale.lib.errors import GametimeError, ThisShouldNeverHappenException
from sizeroyale.lib.img_utils import create_stats_screen, merge_images


logger = logging.getLogger("sizebot")


class Royale:
    def __init__(self, game):
        self.game = game

    async def load(self, data: str):
        self.parser = Parser(self.game, data)

        async for progress in self.parser.parse():
            yield progress

        self.minsize = SV.parse("1mm") if self.parser.minsize is None else SV.parse(self.parser.minsize)
        self.maxsize = SV.parse("4mi") if self.parser.maxsize is None else SV.parse(self.parser.maxsize)
        self.autoelim = True if self.parser.autoelim is None else bool(self.parser.autoelim)
        self.deathrate = Decimal(10) if self.parser.deathrate is None else Decimal(self.parser.deathrate)
        self.arenafreq = Decimal(10) if self.parser.deathrate is None else Decimal(self.parser.deathrate)
        self.unitsystem = "m" if self.parser.unitsystem is None else self.parser.unitsystem
        self.teamwin = False if self.parser.teamwin is None else bool(self.parser.teamwin)

        self.players = self.parser.players
        self.original_player_count = len(self.players)

        self.arenas = self.parser.arenas

        self._bloodbath_events = self.parser.bloodbath_events
        self._day_events = self.parser.day_events
        self._night_events = self.parser.night_events
        self._fatalday_events = self.parser.fatalday_events
        self._fatalnight_events = self.parser.fatalnight_events
        self._feast_events = self.parser.feast_events
        eventsdict = {
            "bloodbath_events": self._bloodbath_events,
            "day_events": self._day_events,
            "night_events": self._night_events,
            "fatalday_events": self._fatalday_events,
            "fatalnight_events": self._fatalnight_events,
            "feast_events": self._feast_events
        }
        self.events = AttrDict(eventsdict)

    @property
    def alive_players(self) -> dict:
        return {k: v for k, v in self.players.items() if self.is_player_alive(v)}

    @property
    def dead_players(self) -> dict:
        return {k: v for k, v in self.players.items() if not self.is_player_alive(v)}

    @property
    def remaining(self) -> int:
        return len(self.alive_players)

    @property
    def current_players(self) -> str:
        """For display purposes only. Don't parse this."""
        return "\n".join([str(p) for p in self.alive_players.values()])

    @property
    def current_teams(self) -> list:
        s = set()
        for player in self.alive_players.values():
            s.add(player.team)
        return list(s)

    async def game_over(self) -> Optional[int]:
        """Returns the winning team, or None if the game isn't over."""
        if self.teamwin:
            if len(self.current_teams) == 1:
                return (self.current_teams[0], merge_images([await p.get_image() for p in self.alive_players.values()]))
            elif len(self.current_teams) == 0:
                return 0
            else:
                return None
        else:
            if self.remaining == 1:
                return ([self.alive_players[k] for k in self.alive_players][0],
                        merge_images([await p.get_image() for p in self.alive_players.values()]))
            elif self.remaining == 0:
                return 0
            else:
                return None

    async def stats_screen(self):
        return await create_stats_screen(self.players)

    def is_player_alive(self, player) -> bool:
        if self.autoelim:
            return player.height > self.minsize and player.height < self.maxsize and player.dead is False
        return player.dead is False

    async def _run_event(self, event: Event, playerpool: Dict[str, Player]) -> dict:
        """Runs an event, returning the string describing what happened and an image."""
        if event.tributes > len(playerpool):
            raise GametimeError("Not enough players to run this event!")
        players = event.get_players(playerpool)

        eventtext = event.fillin(players)
        deaths = []

        logger.log(ROYALE, "[EVENT] " + eventtext)

        def player_by_id(pid):
            return self.players[players.getByIndex(pid - 1).name]

        if event.elims is not None:
            for i in event.elims:
                player_by_id(i).dead = True
                deaths.append(player_by_id(i))

        if event.perps is not None:
            for i in event.perps:
                player_by_id(i).elims += 1

        if event.gives is not None:
            for i, s in event.gives:
                player_by_id(i).give_item(s)

        if event.removes is not None:
            for i, s in event.removes:
                player_by_id(i).remove_item(s)

        if event.clears is not None:
            for i in event.clears:
                player_by_id(i).clear_inventory()

        if event.giveattrs is not None:
            for i, s in event.giveattrs:
                player_by_id(i).give_attribute(s)

        if event.removeattrs is not None:
            for i, s in event.removeattrs:
                player_by_id(i).remove_attribute(s)

        if event.setsizes is not None:
            for i, d in event.setsizes:
                player_by_id(i).height = SV(d)

        if event.sizes is not None:
            for i, d in event.sizes:
                player_by_id(i).change_height(d)

        if event.setsizeranges is not None:
            for i, d1, d2 in event.setsizeranges:
                small, large = minmax(d1, d2)
                d = randRangeLog(small, large)
                player_by_id(i).height = SV(d)

        if event.sizeranges is not None:
            for i, d1, d2 in event.sizeranges:
                da = randRangeLog(d1.amount, d2.amount)
                if d1.changetype == "add":
                    ds = "+"
                elif d1.changetype == "multiply":
                    ds = "x"
                else:
                    raise ThisShouldNeverHappenException
                do = ds + da
                d = Diff(do, changetype = d1.changetype, amount = da)
                player_by_id(i).change_height(d)

        if len(players) == 0:
            eventimage = None
        else:
            eventimage = merge_images([await self.players[p].get_image() for p in players])

        return RunnableEvent(
            text = eventtext,
            image = eventimage,
            players = players,
            deaths = deaths
        )

    def __str__(self):
        outstring = ""
        sublevel = 0

        def add(string):
            nonlocal outstring
            outstring += ("  " * sublevel + string + "\n")
        add(f"Royale {hex(id(self))}:")
        add(f"Autoelim: {self.autoelim!r}, Death Rate: {self.deathrate}, Max Size: {self.maxsize}, Min Size: {self.minsize}")
        add("Players:")
        sublevel += 1
        for n, p in self.players.items():
            add(f"{n!r}: Team: {p.team!r}, Gender: {p.gender!r}, Height: {p.height}, Dead: {p.dead!r}")
            sublevel += 1
            add(f"Image: {p.url!r}")
            add(f"Inventory: {p.inventory!r})")
            sublevel -= 1
        sublevel -= 1
        add("Arenas:")
        sublevel += 1
        for a in self.arenas:
            add(f"{a.name!r}:")
            sublevel += 1
            add(f"Description: {a.description!r},")
            add("Events: ")
            sublevel += 1
            for e in a.events:
                add(f"{e.text}")
                sublevel += 1
                edata = f"Tributes: {e.tributes}, "
                if e.setsizes is not None:
                    edata += f"Set Sizes: {e.setsizes!r}, "
                if e.sizes is not None:
                    edata += "Sizes: " + repr({k: v.original for k, v in e.sizes}) + ", "
                if e.elims is not None:
                    edata += f"Elims: {e.elims!r}, "
                if e.perps is not None:
                    edata += f"Perps: {e.perps!r}, "
                if e.gives is not None:
                    edata += f"Gives: {e.gives!r}, "
                if e.removes is not None:
                    edata += f"Removes: {e.removes!r}, "
                edata += f"Rarity: {e.rarity}"
                add(edata)
                if e.dummies == {}:
                    add("Dummies: {}\n")
                else:
                    add("Dummies: {")
                    sublevel += 1
                    for n, d in e.dummies.items():
                        add(f"{n!r}: {d!r}")
                    sublevel -= 1
                    outstring = outstring.rstrip() + "}\n"
                sublevel -= 1
            sublevel -= 1
            sublevel -= 1
        sublevel -= 1
        add("Events:")
        sublevel += 1
        for et, l in self.events._values.items():
            add(et.replace("_", " ").title() + ":")
            sublevel += 1
            for e in l:
                add(f"{e.text}")
                sublevel += 1
                edata = f"Tributes: {e.tributes}, "
                if e.setsizes is not None:
                    edata += f"Set Sizes: {e.setsizes!r}, "
                if e.sizes is not None:
                    edata += "Sizes: " + repr({k: v.original for k, v in e.sizes}) + ", "
                if e.elims is not None:
                    edata += f"Elims: {e.elims!r}, "
                if e.perps is not None:
                    edata += f"Perps: {e.perps!r}, "
                if e.gives is not None:
                    edata += f"Gives: {e.gives!r}, "
                if e.removes is not None:
                    edata += f"Removes: {e.removes!r}, "
                edata += f"Rarity: {e.rarity}"
                add(edata)
                if e.dummies == {}:
                    add("Dummies: {}\n")
                else:
                    add("Dummies: {")
                    sublevel += 1
                    for n, d in e.dummies.items():
                        add(f"{n!r}: {d!r}")
                    sublevel -= 1
                    outstring = outstring.rstrip() + "}\n"
                sublevel -= 1
            sublevel -= 1
        sublevel -= 1

        return outstring

    def __repr__(self):
        return f"Royale(autoelim={self.autoelim!r}, deathrate={self.deathrate!r}, maxsize={self.maxsize!r}, minsize={self.minsize!r}, players={self.players!r}, arenas={self.arenas!r}, events={self.events!r})"
