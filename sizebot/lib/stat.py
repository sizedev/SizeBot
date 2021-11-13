import math
from typing import Union


class Stat:
    def __init__(self, name: str, scalepower: int = 1, default_base: Union[float, callable] = None, settable=True):
        self.name = name
        self.scalepower = scalepower
        self.get_default_base = default_base if callable(default_base) else lambda user: default_base
        self.settable = settable

    def get_scaled(self, user, scale: float = None):
        if scale is None:
            scale = user.scale
        base_value = self.get_base(user)
        scaled_value = base_value * (scale ** self.scalepower)
        return scaled_value

    def get_base(self, user):
        base_value = None
        if self.settable:
            base_value = user.base_stats.get(self.name)
        if base_value is None:
            base_value = self.get_default_base(user)
        return base_value


SV = WV = lambda x: x


class UserStat:
    def __init__(self, user, stat: Stat):
        self.user = user
        self.stat = stat

    def get_scaled(self, scale: float = None):
        return self.stat.get_scaled(self.user, scale)

    def get_base(self):
        return self.stat.get_base(self.user)


average_height = 1.754
average_walkperhour = 5630
average_runperhour = 10729
average_swimperhour = 3219
average_climbperhour = 4828
average_crawlperhour = 2556
walkstepsperhour = 6900
runstepsperhour = 10200


def terminal_velocity(m, k):
    g = 9.807
    return math.sqrt(g * m / k)


class UserStats:
    stats = [
        Stat("height"),
        Stat("weight", scalepower=3),
        Stat("hairlength"),
        Stat("taillength"),
        Stat("earheight"),
        Stat("liftstrength", default_base=WV("18143.7")),
        Stat("footlength", default_base=lambda user: user.stats.base_height * (1 / 7)),
        Stat("shoesize", fucked=True),
        Stat("footwidth", default_base=lambda user: user.stats.base_footlength * ((2 / 3) if user.pawtoggle else (2 / 5))),
        Stat("toeheight", default_base=lambda user: user.stats.base_height * (1 / 65)),
        Stat("shoeprintdepth", default_base=lambda user: user.stats.base_height * (1 / 135)),
        Stat("pointerlength", default_base=lambda user: user.stats.base_height * (1 / 17.26)),
        Stat("thumbwidth", default_base=lambda user: user.stats.base_height * (1 / 69.06)),
        Stat("fingerprintdepth", default_base=lambda user: user.stats.base_height * (1 / 35080)),
        Stat("threadthickness", default_base=0.001016, settable=False),
        Stat("hairwidth", default_base=lambda user: user.stats.base_height * (1 / 23387)),
        Stat("nailthickness", default_base=lambda user: user.stats.base_height * (1 / 2920)),
        Stat("eyewidth", default_base=lambda user: user.stats.base_height * (1 / 73.083)),
        Stat("jumpheight", default_base=lambda user: user.stats.base_height * (1 / 3.908)),
        Stat("walkperhour", default_base=lambda user: average_walkperhour * (user.stats.base_height / average_height)),
        Stat("runperhour", default_base=lambda user: average_runperhour * (user.stats.base_height / average_height)),
        Stat("swimperhour", default_base=lambda user: average_swimperhour * (user.stats.base_height / average_height)),
        Stat("climbperhour", default_base=lambda user: average_climbperhour * (user.stats.base_height / average_height), settable=False),
        Stat("crawlperhour", default_base=lambda user: average_crawlperhour * (user.stats.base_height / average_height), settable=False),
        Stat("walksteplength", default_base=lambda user: user.stats.base_walkperhour / walkstepsperhour),
        Stat("runsteplength", default_base=lambda user: user.stats.base_runperhour / runstepsperhour),
        Stat("climbsteplength", default_base=lambda user: user.stats.base_height * (2 / 5)),
        Stat("crawlsteplength", default_base=lambda user: user.stats.base_height * (1 / 2.577)),
        Stat("swimsteplength", default_base=lambda user: user.stats.base_height * (6 / 7)),
        Stat("terminalvelocity", default_base=lambda user: terminal_velocity(user.stats.base_weight), scalepower=0.5, settable=False)
    ]

    def __init__(self, user):
        for stat in self.stats:
            setattr(self, stat.name, property(lambda self: stat.get_scaled(user)))
            setattr(self, f"base_{stat.name}", property(lambda self: stat.get_base(user)))


statdict = {
    s.name: s for s in
}

miniw = w.calc((1 / 12), userdata)
