import math

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.userdb import User
from sizebot.lib.units import SV

G = 9.81
STOMP_G = 11.5

STEP_FACTOR = 0.07
STOMP_FACTOR = 0.5
JUMP_FACTOR = 0.43

def joules_to_mag(joules: float) -> Decimal:
    # This might not be super accurate.
    return Decimal(2/3) * Decimal(math.log10(joules)) - Decimal(3.2)

def mag_to_radius(mag: float) -> SV:
    return SV(Decimal(math.exp(Decimal(mag) / Decimal(1.01) - Decimal(0.13))) * 1000)

def mag_to_name(mag: float) -> str:
    if mag < 1:
        return "no"
    elif mag < 3:
        return "unnoticeable"
    elif mag < 4:
        return "minor"
    elif mag < 5:
        return "light"
    elif mag < 6:
        return "moderate"
    elif mag < 7:
        return "strong"
    elif mag < 8:
        return "major"
    elif mag < 9:
        return "great"
    elif mag < 10:
        return "extreme"
    elif mag < 22:
        return "apocalyptic"
    else:
        return "earth-ending"

def scale_to_joules(user: User, g: float, factor: float) -> int:
    return math.floor((user.weight * Decimal(0.4536)) / 2 * Decimal(g) * (Decimal(factor) * user.scale))

def step_joules(user: User) -> int:
    return scale_to_joules(user, G, STEP_FACTOR)

def stomp_joules(user: User) -> int:
    return scale_to_joules(user, STOMP_G, STOMP_FACTOR)

def jump_joules(user: User) -> int:
    return scale_to_joules(user, G, JUMP_FACTOR)
