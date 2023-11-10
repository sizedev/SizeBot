import math

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.userdb import User
from sizebot.lib.units import SV

G = 9.81
STOMP_G = 11.5

STEP_FACTOR = 0.035
STOMP_FACTOR = 0.5
JUMP_FACTOR = 1

def joules_to_mag(joules: float) -> Decimal:
    # This might not be super accurate.
    return Decimal(2/3) * Decimal(math.log10(joules)) - Decimal(3.2)

def mag_to_radius(mag: float) -> SV:
    return SV(Decimal(math.exp(Decimal(mag - 1) / Decimal(1.01) - Decimal(0.13))) * 1000)

def mag_to_name(mag: float) -> str:
    if mag < 1:  # 0 - 1
        return "no"
    elif mag < 3:  # 1 - 3
        return "unnoticeable"
    elif mag < 4:  # 3 - 4
        return "minor"
    elif mag < 5:  # 4 - 5
        return "light"
    elif mag < 6:  # 5 - 6
        return "moderate"
    elif mag < 7:  # 6 - 7
        return "strong"
    elif mag < 8:  # 7 - 8
        return "major"
    elif mag < 9:  # 8 - 9
        return "great"
    elif mag < 10:  # 9 - 10
        return "extreme"
    elif mag < 13:  # 10 - 13
        return "unprecedented"
    elif mag < 21:  # 13 - 21
        return "apocalyptic"
    elif mag < 22:  # 22 - 23
        return "earth-cracking"
    else:  # 23 - inf
        return "earth-crumbling"

def scale_to_joules(user: User, g: float, factor: float) -> Decimal:
    return Decimal((user.weight * Decimal(0.4536)) / 2 * Decimal(g) * (Decimal(factor) * user.scale))

def step_joules(user: User) -> int:
    return scale_to_joules(user, G, STEP_FACTOR)

def stomp_joules(user: User) -> int:
    return scale_to_joules(user, STOMP_G, STOMP_FACTOR)

def jump_joules(user: User) -> int:
    return scale_to_joules(user, G, JUMP_FACTOR)
