import logging

from math import acos, pi
from sizebot.lib.units import SV, WV

GRAVITY = 980.7  # cm/s^2
WATER_SURFACE_TENSION = 72.8  # dy/cm

logger = logging.getLogger("sizebot")

# WV = grams
# SV = meters

def can_walk_on_water(weight: WV, footlength: SV, footwidth: SV) -> bool:
    foot_cirum = (footlength * 2 * 100) + (footwidth * 2 * 100)
    foot_force_frac = (float(weight) * GRAVITY) / (WATER_SURFACE_TENSION * float(foot_cirum) * 2)
    logger.info(f"{foot_force_frac=}")
    return 0 <= foot_force_frac < 1
