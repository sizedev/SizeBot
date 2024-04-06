import math
from typing import Tuple

from sizebot.lib.digidecimal import Decimal
from sizebot.lib.units import TV, WV, SV


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
    m = basemass * (scale ** Decimal(3))
    h = altitude
    g = Decimal("9.807")
    k = Decimal("0.24") * (scale ** Decimal(2))

    t = Decimal(math.sqrt(m / (g * k))) * Decimal(math.acosh(Decimal(math.exp(h * k / m))))
    vel = Decimal(math.sqrt(g * m / k)) * Decimal(math.tanh(t * Decimal(math.sqrt(g * k / m))))

    # calculate feelslike
    TWENTY_FIVE_SIXTHS = Decimal(25) / Decimal(6)
    step2 = Decimal(math.sqrt(Decimal(1) / basemass))
    step3 = Decimal(math.sqrt(basemass))
    step4 = Decimal(math.atanh((Decimal("0.156436") * vel) / Decimal(math.sqrt(basemass))))
    step5 = -Decimal(math.cosh(step2 * step3 * step4))
    feelslike = m * Decimal(math.log(Decimal(math.pow(-step5, TWENTY_FIVE_SIXTHS))))

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
