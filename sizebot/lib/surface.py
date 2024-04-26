from math import acos, pi
from sizebot.lib.units import SV, WV

GRAVITY = 9.807  # m/s^2
WATER_SURFACE_TENSION = 0.0728  # N/m

def can_walk_on_water(weight: WV, footlength: SV, footwidth: SV) -> bool:
    foot_cirum = (footlength * 2) + (footwidth * 2)
    foot_force_frac = ((float(weight) / 1000) * GRAVITY) / (WATER_SURFACE_TENSION * float(foot_cirum) * 2)
    return 0 <= foot_force_frac < 1
