import math
from typing import Tuple

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import TV, WV, SV


def terminal_velocity(g, m, k):
    return math.sqrt(g * m / k)


def freefall(basemass: WV, altitude: SV, scale: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
    """
    If dropped, how long does it take for person to hit ground

    basemass: original mass of personal (grams)
    altitude: height dropped from (meters)
    scale: height multiplier

    returns tuple of:
        Time of fall (secs)
        Maximum velocity (m/s)
        Terminal velocity (m/s)
    """
    basemass = basemass / Decimal(1000)
    m = basemass * (scale ** 3)
    h = altitude
    g = Decimal("9.807")
    k = Decimal("0.24") * (scale ** 2)

    t = math.sqrt(m / (g * k)) * math.acosh(math.exp(h * k / m))
    vel = math.sqrt(g * m / k) * math.tanh(t * math.sqrt(g * k / m))
    feelslike = m * math.log(-(-math.cosh(math.sqrt(1 / basemass) * math.sqrt(basemass) * math.atanh((0.156436 * vel) / math.sqrt(basemass)))) ** (25 / 6))

    return TV(t), SV(vel), SV(feelslike)

# https://www.omnicalculator.com/physics/free-fall-air-resistance#how-to-calculate-air-resistance
# If dropped, how long does it take for person to hit ground
#
# Input:
#     Size
#     Distance
# Output:
#     Time
#
# t = sqrt(m/(g*k))*acosh(exp(h*k/m))
# v = sqrt((m*g)/k)) * tanh(sqrt((g*k)/m))
#
# IN
# m       Mass                        ? kg        (scales ^ 3)
# h       Altitude                    ? m
# g       Gravitational acceleration  9.807 m/s^2 (constant)
# k       Air resistance              0.24 kg/m   (scales ^ 2)
#
# OUT
# t       Time of fall                ? sec
# vel     Maximum velocity            ? m/s
# vmax    Terminal Velocity           ? m/s
#
#         g = 9.807
#         t = sqrt(m/(g*k))*acosh(exp(h*k/m))
#       vel = sqrt(g*m/k)*tanh(t*sqrt(g*k/m))
#      vmax = sqrt(g*m/k)
# feelslike = m * log(-(-cosh(sqrt(1/m) * sqrt(m) * atanh((0.156436 * v)/sqrt(m))))**(25/6))
