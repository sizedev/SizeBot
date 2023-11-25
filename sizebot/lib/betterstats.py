from typing import Union
from decimal import Decimal
from sizebot.lib.units import SV, TV, WV
from sizebot.lib.userdb import User


Unit = Union[SV, TV, WV, Decimal, bool, str]

class Stat:
    def __init__(self, key: str, name: str, equation: callable[[User], Unit], exponent: int = 1):
        self.key = key
        self.name = name
        self.equation = equation
        self.exponent = exponent

    def from_user(self, user: User) -> Unit:
        return self.equation(user)
