from math import acos, pi
from sizebot.lib.stats import GRAVITY
from sizebot.lib.units import SV, WV

WATER_SURFACE_TENSION = 72.8  # mN/m

def can_walk_on_water(weight: WV, footlength: SV, footwidth: SV) -> bool:
    foot_cirum = (footlength * 2) + (footwidth * 2)
    foot_force_frac = ((weight / 1000) * GRAVITY) / (WATER_SURFACE_TENSION * foot_cirum * 2)
    angle = acos(foot_force_frac)
    return angle < (pi / 2)
