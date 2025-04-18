import math

from sizebot.lib.userdb import User
from sizebot.lib.units import SV, Decimal

G = 9.81
STOMP_G = 11.5

STEP_FACTOR = 0.035
STOMP_FACTOR = 0.5
JUMP_FACTOR = 1

BREATH_JOULES = 0.025
POKE_JOULES = 8
HEARTBEAT_JOULES = 5.38E-9
TYPE_JOULES = 2.5E-3


def joules_to_mag(joules: float) -> Decimal:
    # This might not be super accurate.
    return Decimal(2 / 3) * Decimal(math.log10(joules)) - Decimal(3.2)


def mag_to_radius(mag: float) -> SV:
    return SV(Decimal(math.exp(Decimal(mag - 1) / Decimal(1.01) - Decimal(0.13))) * 1000)


def mag_to_name(mag: float) -> str:
    b = ""
    if mag < 1:  # 0 - 1
        r = "no quake"
    elif mag < 3:  # 1 - 3
        r = "unnoticeable"
    elif mag < 4:  # 3 - 4
        r = "minor"
    elif mag < 5:  # 4 - 5
        r = "light"
    elif mag < 6:  # 5 - 6
        r = "moderate"
    elif mag < 7:  # 6 - 7
        r = "strong"
    elif mag < 8:  # 7 - 8
        r = "major"
    elif mag < 9:  # 8 - 9
        r = "great"
    elif mag < 10:  # 9 - 10
        r = "extreme"
    elif mag < 13:  # 10 - 13 [at this point I'm making s*** up]
        r = "unprecedented"
    elif mag < 21:  # 13 - 21 [I did do research tho, I didn't just pull this out of my butt]
        r = "apocalyptic"
    elif mag < 22:  # 21 - 23
        r = "earth-cracking"
    elif mag < 25:  # 23 - 25
        d = 10 ** (mag - 22)
        r = "earth-crumbling"
        b = f" x{d:,.0f}"
    elif mag < 32:  # 25 - 32
        d = 10 ** (mag - 25)
        r = "sun-shattering"
        b = f" x{d:,.0f}"
    elif mag < 63:  # 32 - 63
        d = 10 ** (mag - 32)
        r = "galaxy-collapsing"
        b = f" x{d:,.0f}"
    else:  # 63+
        d = 10 ** (mag - 63)
        r = "universe-ending"
        b = f" x{d:,.0f}"
    return r.title() + b


def scale_to_joules(user: User, g: float, factor: float) -> Decimal:
    return (Decimal(user.weight / 1000) / 2) * (Decimal(g) * Decimal(user.scale)) * Decimal(factor)


def step_joules(user: User) -> Decimal:
    return scale_to_joules(user, G, STEP_FACTOR)


def stomp_joules(user: User) -> Decimal:
    return scale_to_joules(user, STOMP_G, STOMP_FACTOR)


def jump_joules(user: User) -> Decimal:
    return scale_to_joules(user, G, JUMP_FACTOR)


def breath_joules(user: User) -> Decimal:
    return Decimal(BREATH_JOULES) * (user.scale ** 3)


def poke_joules(user: User) -> Decimal:
    return Decimal(POKE_JOULES) * (user.scale ** 3)


def heartbeat_joules(user: User) -> Decimal:
    return Decimal(HEARTBEAT_JOULES) * (user.scale ** 3)


def type_joules(user: User) -> Decimal:
    return Decimal(TYPE_JOULES) * (user.scale ** 3)
