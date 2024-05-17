from __future__ import annotations
from collections.abc import Callable

from colored import colors, style, fg, bg, attr
import os
from getch import getch

ESC = "\033"
CLEAR_SCREEN = ESC + "[2J"
RESET_TERMINAL = ESC + "c"
CURSOR_HOME = ESC + "H"


attrlist = [(n, v) for n, v in style.names.items()]
attrlist.insert(0, ("None", None))
colorlist = [(n, v) for v, n in enumerate(colors.names)]
colorlist.insert(0, ("None", None))


def draw(indexes: list[Index], sel: int):
    code = "".join(i.code for i in indexes)
    names = "/".join(i.codename for i in indexes)

    print(f"  {code}{names}{style.RESET}")
    print()

    vals = "".join(f"{str(i.val):<5}" for i in indexes)
    print(" " + vals)
    selpadding = sel * 5 + 1
    print((selpadding * " ") + "^")

    for i, index in enumerate(indexes):
        print(("> " if sel == i else "  ") + str(index))


class Index:
    def __init__(self, name: str, options: list[tuple[str, int]], mapper: Callable[[int], str], val: int = 0):
        self.name = name
        self.options = options
        self.mapper = mapper
        self.index = val

    def jump(self, jumpAmt: int):
        self.index = min(max(0, self.index + jumpAmt), len(self.options) - 1)

    @property
    def val(self) -> int:
        name, val = self.options[self.index]
        return val

    @property
    def code(self) -> str:
        if self.val is not None:
            return self.mapper(self.val)
        else:
            return ""

    @property
    def codename(self) -> str:
        name, val = self.options[self.index]
        return name

    def __str__(self) -> str:
        return f"{self.name:>5}: {str(self.val):>4} {self.code:>3}{self.codename}{style.RESET}"


def main():

    os.system("")

    indexes = [
        Index("FG", colorlist, fg),
        Index("BG", colorlist, bg),
        Index("ATTR", attrlist, attr)
    ]
    sel = 0

    running = True
    k = ""
    while running:
        print(RESET_TERMINAL)
        draw(indexes, sel)
        print()
        print(k)
        k = getch()
        if k == "q":
            running = False
        elif k in ("KEY_UP", "KEY_S_UP"):
            jump = 1
            if k == "KEY_S_UP":
                jump = 10
            indexes[sel].jump(jump)
        elif k in ("KEY_DOWN", "KEY_S_DOWN"):
            jump = -1
            if k == "KEY_S_DOWN":
                jump = -10
            indexes[sel].jump(jump)
        elif k == "KEY_LEFT":
            sel = max(0, sel - 1)
        elif k == "KEY_RIGHT":
            sel = min(sel + 1, len(indexes) - 1)


main()
