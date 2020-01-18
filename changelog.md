# SizeBot 3.5 Changelog

## Additions

- Added customizable foot length with `&setfoot`.
- Added shoeprint depth, nail thickness, clothing thread thickness, eye width, walk speed, and run speed to stats and comparisons.
- Added a link to a visual comparison when using `&compare`.
- Slow changes now support stop conditions, either a time or a size.
- The `&help` command now supports arguments for detailed info on a specific command, as in `&help [command]`.
    - Many commands now have helpful aliases, which you can find by running `&help [command]`.
- Added the ability to use exponents in changes, for instance `&change ^ 2`.
    - For instance, running `&change ^ 2` while 10ft tall would set you to a height that makes you appear 10 ft tall to a 10 ft tall person.
- Inches are now displayed in fraction increments in sizetags.
- Added a new command, `&objcompare`, which lets you see what object you are closest to in height and weight.
- Added a `&ping` command, to see if it's us who's lagging, or it's just Discord again.

## Changes

- The help command, and all SizeBot documentation from here on out, now uses `<argument>` for required arguments, and `[argument]` for optional arguments, as per Unix-style formatting.
- Stats and comparisons now come in the form of clean, compact embeds.
- Slow changes now operate on a 6-second loop, so all slow changes are constant and consistent.
- Unregistering is far more easy to confirm, requiring you to click an emoji, rather than copy and paste a hex code.

## Fixes

- Slow changes now save and catch up if SizeBot crashes.
- Most math was either inaccurate or slightly wrong, which is now fixed.

## New Commands and New Command Syntax

### New Commands

- `&objcompare`
- `&ping`

### New Command Syntax

- `&slowchange <rate> [stop condition]`
