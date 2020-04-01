# SizeBot3½ Style Guide

## Use the .flake8

Do it.

Use flake8 linter, use the include .flake8 file in the root folder.

## Naming Your Stuff

* Variables should be named in `snake_case`.
* Functions should be named in `snake_case` too.<sup>1</sup>
  * Getters usually start with `get`.
  * Checkers usually start with `is`.
* Constants should be named using `ALL_CAPS_SNAKE_CASE`.
* Classes should be named in `UppercaseWords`.

## Imports

Imports are grouped by blank lines in these categories: builtins, externals, discord stuff, and internals. In these groups, we sort by:
  * import vs. from
  * in order of A-Z
  * in order of deepness

Multi-import lines (e.g.: `from sizebot.lib.constants import emojis, ids`) should be in alphabetical order.

Example:

```python
import builtins
import inspect
import itertools
import logging
import math
from copy import copy

import toml

import discord

from sizebot import conf
from sizebot.cogs import thistracker
from sizebot.lib import userdb, utils
from sizebot.lib.constants import emojis, ids
from sizebot.lib.decimal import Decimal
from sizebot.lib.objs import objects
from sizebot.lib.units import Rate, Mult, SV, WV, TV
```

-------

<sup>1</sup> Much to DigiDuncan's dismay.