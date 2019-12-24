from pathlib import Path

import appdirs
appname = "SizeBot"
appauthor = "DigiDuncan"
confdir = Path(appdirs.user_data_dir(appname, appauthor))


# Version
version = "3AAH.0.0.b4"

# ASCII art
banner = r"""
. _____ _        ______       _   _____ .
./  ___(_)       | ___ \     | | |____ |.
.\ `--. _ _______| |_/ / ___ | |_    / /.
. `--. \ |_  / _ \ ___ \/ _ \| __|   \ \.
./\__/ / |/ /  __/ |_/ / (_) | |_.___/ /.
.\____/|_/___\___\____/ \___/ \__\____/ ."""

# Constants
sizebotuser_roleid = 562356758522101769
enspace = "\u2002"
printtab = enspace * 4

idfilepath = confdir / "ids.txt"
hexfilepath = confdir / "hexstring.txt"
authtokenpath = confdir / "authtoken.txt"
prefix = "&"

description = ("SizeBot3 is a complete rewrite of SizeBot for the Macropolis and, later, Size Matters server.\n"
               "SizeBot3AndAHalf is a refactorization for SB3 and adds database support.\n"
               "Written by DigiDuncan.\n"
               "The SizeBot Team: DigiDuncan, Natalie, Kelly, AWK_, Benyovski, Arceus3521, Surge The Raichu.")


def load():
    print(f"Loading configuration from {confdir}")
