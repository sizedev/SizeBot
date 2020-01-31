# SizeBot 3.5 Changelog

## Additions

- Added customizable foot length with `&setfoot`.
- Added shoeprint depth, nail thickness, clothing thread thickness, eye width, walk speed, run speed, and viewing angle to stats and comparisons.
- Added a link to a visual comparison when using `&compare`.
- Slow changes now support stop conditions, either a time or a size.
- The `&help` command now supports arguments for detailed info on a specific command, as in `&help [command]`.
    - Many commands now have helpful aliases, which you can find by running `&help [command]`.
- Added the ability to use exponents in changes, for instance `&change ^ 2`.
    - For instance, running `&change ^ 2` while 10ft tall would set you to a height that makes you appear 10 ft tall to a 10 ft tall person.
- Inches are now displayed in fraction increments in sizetags.
- Added a new command, `&objcompare`, which lets you see what object you are closest to in height and weight.
    - Displays different, random comparisons from a list of close comparisons on every run.
    - Includes fractional output to the nearest eighth, and accuracy percentages!
- Added an Agreements Leaderboard.
    - Sending either `^`, `this`, `agree`, or one of many various "this" emotes after a message, or reacting to a message with one of those emotes, will give that user an "agreement point."
    - The leaderboard for this can be displayed with `&leaderboard`.
- Added a `&ping` command, to see if it's us who's lagging, or it's just Discord again.
- Added a new command, `&naptime`, which kicks you from any voice channel you're in after a set duration.
- Users now have the ability to use some simple SizeBot functions in DMs, including `&roll`, `&help`, and `&about`.
- You can now edit a failed command message, and it will rerun the command.
- Some fun easter eggs were added to SizeBot as well! Good luck finding them! :wink:

## Changes

- The help command, and all SizeBot documentation from here on out, now uses `<argument>` for required arguments, and `[argument]` for optional arguments, as per Unix-style formatting.
- Stats and comparisons now come in the form of clean, compact embeds.
- Slow changes now operate on a 6-second loop, so all slow changes are constant and consistent.
- Slow changes now use a "rate" as input, for instance `&slowchange 1m/s`.
- Unregistering is far more easy to confirm, requiring you to click an emoji, rather than copy and paste a hex code.
- Changed the way 0 and Infinity are handled as heights, making their stats and comparisons make much more sense.
- The about section now is more accurate, and has new information.
- `&weightunits` and `&heightunits` have been merged into the more easily remembered and cleanly displayed `&units`.
- `&setbaseheight` and `&setbaseweight` have been merged into `&setbase`, which automatically determines which value to change based on the units you give it.
    - `&setbase 5ft` sets your base height to 5ft.
    - `&setbase 100lb` sets your base weight to 100lb.
    - `&setbase 5ft 100lb` sets both base height and base weight simultaneously.
    - `&setbaseheight` and `&setbaseweight` still exist for convenience.

## Fixes

- Slow changes now save and catch up if SizeBot crashes.
    - Many other weird undocumented behaviors with slow changes should also be resolved.
- Most math was either inaccurate or slightly wrong, which is now fixed.
- Unicode in nicknames is now handled correctly.
- Some smallish numbers were being displayed in scientific notation, which is no longer the case.

## New Commands and New Command Syntax

### New Commands

- `&objcompare`
- `&ping`
- `&setbase <height/weight> [height/weight]`
- `&naptime <duration>`
- `&units`

### New Command Syntax

- `&slowchange <rate> [stop condition]`
