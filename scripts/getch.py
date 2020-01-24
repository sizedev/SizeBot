class _Getch:
    """Gets a single character from standard input.  Does not echo to the screen."""

    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self):
        ch = self.impl()
        sequences = {
            "\x1b[A": "KEY_UP",
            "\x1b[B": "KEY_DOWN",
            "\x1b[C": "KEY_RIGHT",
            "\x1b[D": "KEY_LEFT",
            "\x1b[1;2A": "KEY_S_UP",
            "\x1b[1;2B": "KEY_S_DOWN",
            "\x1b[1;2C": "KEY_S_RIGHT",
            "\x1b[1;2D": "KEY_S_LEFT"
        }
        while ch in [s[:len(ch)] for s in sequences.keys()]:
            if ch in sequences:
                return sequences[ch]
            ch += self.impl()
        return ch


class _GetchUnix:
    def __init__(self):
        import tty
        import sys

    def __call__(self):
        import sys
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()
