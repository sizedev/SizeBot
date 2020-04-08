# SizeBot 3.5 Changelog

## Additions

- SizeBot now has rudimentary multi-guild support! (β)
    - You can copy your profile from one guild to the other with `&copy`.
    - Keeping your profiles on multiple servers synced to each other is not yet possible.
    - **NOTE:** *This is in beta stages, and is being rolled out slowly. Contact DigiDuncan if you are interested in having SizeBot on your server.*
- Added customizable foot length with `&setfoot`. You can turn off custom foot length with `&resetfoot`.
- Added shoeprint depth, nail thickness, clothing thread thickness, eye width, walk speed, run speed, and viewing angle to stats and comparisons.
- Added a link to a visual comparison when using `&compare`.
- Slow changes now support stop conditions, either a time or a size.
- Gender is now customizable, though it doesn't do much right now, with `&setgender`. Turn off "hard gender" with `&resetgender`.
    - Gender will try to be infered if you have an gender roles assigned to you. This is known as "soft gender."
- The `&help` command now supports arguments for detailed info on a specific command, as in `&help [command]`.
    - Many commands now have helpful aliases, which you can find by running `&help [command]`.
- Added the ability to use exponents in changes, for instance `&change ^ 2`.
    - For instance, running `&change ^ 2` while 10ft tall would set you to a height that makes you appear 10 ft tall to a 10 ft tall person.
- Inches are now displayed in fraction increments in sizetags.
- Added a new command, `&objcompare`, which lets you see what object you are closest to in height and weight.
    - Displays different, random comparisons from a list of close comparisons on every run.
    - Includes fractional output to the nearest eighth, and accuracy percentages!
- Added a new command, `&lookat`, which allows you to see what an object or person looks like to you.
    - Displays a different stats screen based on whether you're looking at a person, or an object.
    - To look at an object, use `&lookat <object>`, e.g.: `&lookat lego brick`
    - To look at a person, use `&lookat <@user>`, e.g.: `&lookat @Kelly`
    - To look at a raw height (interpreted as a person), use `&lookat <height>`, e.g.: `&lookat 5'11`
- Added the ability for administrators to set "edge" users, one "smallest" and one "largest", whose size will be auto-set to be the lowest or highest on the server.
    - Use `&edges` to see who is currently set to be the edge users.
    - Administrators can use `&setsmallest <@user>` and `&setlargest <@user>` to set the edge users, and `&clearsmallest` and `&clearlargest` to remove them.
- Added an Agreements Leaderboard.
    - Sending either `^`, `this`, `agree`, or one of many various "this" emotes after a message, or reacting to a message with one of those emotes, will give that user an "agreement point."
    - The leaderboard for this can be displayed with `&leaderboard`.
- Added some non-size commands for fun:
    - Added a new command, `&naptime <duration>`, which kicks you from any voice channel you're in after a set duration.
    - Added `&color <hex/rgb/hsv/cmyk> <value>`, which let's you see information about different colors.
- Added a `&ping` command, to see if it's us who's lagging, or it's just Discord again.
- Users now have the ability to use some simple SizeBot functions in DMs, including `&roll`, `&help`, and `&about`.
- You can now edit a failed command message, and it will rerun the command.
- Mei and SizeBot are now friends.
- Some fun easter eggs were added to SizeBot as well! Good luck finding them! :wink:

## Changes

- The help command, and all SizeBot documentation from here on out, now uses `<argument>` for required arguments, and `[argument]` for optional arguments, as per Unix-style formatting.
- Stats and comparisons now come in the form of clean, compact embeds.
- Slow changes now operate on a 6-second loop, so all slow changes are constant and consistent.
- Slow changes now use a "rate" as input, for instance `&slowchange 1m/s`.
- Unregistering is far more easy to confirm, requiring you to click an emoji, rather than copy and paste a hex code.
- Changed the way 0 and Infinity are handled as heights, making their stats and comparisons make much more sense.
- The about section now is more accurate, and has new information.
- `&weightunits` and `&heightunits` have been merged into the more easily remembered and cleanly displayed `&units`, along with a new `&objects` command.
- `&setbaseheight` and `&setbaseweight` have been merged into `&setbase`, which automatically determines which value to change based on the units you give it.
    - `&setbase 5ft` sets your base height to 5ft.
    - `&setbase 100lb` sets your base weight to 100lb.
    - `&setbase 5ft 100lb` sets both base height and base weight simultaneously.
    - `&setbaseheight` and `&setbaseweight` still exist for convenience.

## Fixes

- **The entire codebase was rewritten from the ground up.**
- Slow changes now save and catch up if SizeBot crashes.
    - Many other weird undocumented behaviors with slow changes should also be resolved.
- Most math was either inaccurate or slightly wrong, which is now fixed.
- SizeBot should no longer crash seemingly randomly.
- Users having their height set to zero and running stats or compare should no longer make less sense than the concept itself does.
- Unicode in nicknames is now handled correctly.
- Some smallish numbers were being displayed in scientific notation, which is no longer the case.
- A bug where sometimes SizeBot would spit way too many decimal places out should be corrected.
- All commands should now give feedback to the user, so you actually know if something happened.
- Nicknames should now update as soon as your size changes, and not just when you first type.


## New Commands and Changed Command Syntax

### New Commands

`# TODO: Work on this section.`

### Changed Command Syntax

`# TODO: Work on this section.`
