import decimal

Decimal = decimal.Decimal

# Configure decimal module
decimal.getcontext()
context = decimal.Context(prec = 120, rounding = decimal.ROUND_HALF_EVEN,
                          Emin = -9999999, Emax = 999999, capitals = 1, clamp = 0, flags = [],
                          traps = [decimal.Overflow, decimal.DivisionByZero, decimal.InvalidOperation])
decimal.setcontext(context)
