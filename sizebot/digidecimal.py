import decimal

Decimal = decimal.Decimal

# Configure decimal module
decimal.getcontext()
context = decimal.Context(
    prec = 120, rounding = decimal.ROUND_HALF_EVEN,
    Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
    traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)


def roundDecimal(d, accuracy = 0):
    places = Decimal("10") ** -accuracy
    return d.quantize(places)


def roundDecimalHalf(number):
    return roundDecimal(number * Decimal("2")) / Decimal("2")


# Format a Decimal to a string, removing exponents and trailing zeroes after the decimal
def trimzeroes(d):
    # `normalize()` removes ALL trailing zeroes, including ones before the decimal place
    # `+ 0` readds the trailing zeroes before the decimal place, if necessary
    return d.normalize() + 0
