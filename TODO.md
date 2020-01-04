## SizeBot3½

* ~~Don't import * globalsb~~
* ~~Clean up all the imports really~~
* ~~Follow and document style conventions~~
* ~~Prevent that error we keep getting on readuser~~
* Come up with a consistent versioning scheme. (Digi will be anal about this.)
* Setup develop branch
* Host Sizebot Unstable on VPS
    * Setup automatic deployment of develop branch commits
* ~~Migrate legacy User constants to new User object~~
* ~~Formatting~~
    * ~~Replace .format() with f-strings~~
    * ~~Fix allowbrackets~~
    * ~~Fix flake8 linting to check for more issues~~
* ~~Fix Unicode handling for nicknames (if this is even possible)~~
* ~~Make a custom emoji dictionary~~
* Commands
    * Make register commands easier to use and give better use output (simpler usage and better defaults)
    * Change the way &slowchange works (&slowchange \<rate\>)
    * Create convert command (&convert \<size\> \<new unit\>)
    * Custom base height/weight for raw compares
    * Create eval command (for devs only)
    * Help command
    * Implement SB3's &roll command.
* Make SizeBot respond to DMs in a helpful way.
    * Allow users to use DM-safe commands in DMs (about, help, bug, donate, convert, roll) \[are there more?\]
    * Otherwise, tell them they have to other commands in a server.
* Separate command logic into modules.
    * Register commands
    * Size change commands
    * Size comparison commands
* Setup testing.
    * Register commands
    * Size change command
    * Size comparison commands
    * Dice rolling
    * Size conversion
* DigiSV:
    * Custom trigger points for units (millimeters triggers 1 degree of magnitude early, megameters triggers 1 degree late.)
    * Flag some units as only input units and not display units.
    * Fix the giant if statements<sup>?</sup>
    * Make no units ambiguous. (universes, Earths, Suns...)
    * Any value under 0.001ym gets displayed as 0 (currently not true for stats)
* Basic English syntax for some commands.
* Make foot length optionally customizable.
* Command metadata
    * Can it be used in DMs?
    * Help strings
    * Remove brackets?
    * etc...
* Make DigiLogger and DigiFormatter be imported from their seperate things instead of copy+pasting them in to the folder.
* Sudo command<sup>?</sup>
* Question of the Day
    * Users can submit questions
    * These get posted to a voting channel for mods only.
    * Mods react to the submissions with emotes (:voteyes:/:voteno:)
    * If it gets accepted, it gets added to the pool.
    * A random question (with credit) is posted to a question of the day channel every morning.
* Change SizeBot's name on certain special dates
* This Points: if someone posts ^, or :this:, or similar, give a This Point to the person above (unless that person also posted a "this", in which case, give it to the person above that, etc.)
* Future proofing.
    * Make module functions that make command code easy to read, work with, and make new commands. \[Digi calls this "the SizeAPI"\]

#### Figure out database schema.

## SizeBot4

* Migrate to MariaDB
    * Make repeating tasks check the database every X time instead of asyncio tasks that are unwieldy
    * Guilds
    * Members
    * "Characters"
    * Winks
* Switchable user profiles (create characters, switch between them)
* Switch some things to embeds
* Replace digiSV with dunit
* Add support for multiple guilds
* Allow users to store character pictures
* Autostop option for slowchange
* Custom emojis trigger events
* Generate user "cards"
* Compare yourself to objects of similar size
* Auto-role based on current size option (optional for user)
* Allow users to change other users (on, blacklist, whitelist, off)
* NSFW stats<sup>?</sup>
* More customizables
* Natural language chat/help (like a virtual assistant) \[needs a name\]
* Per-guild customizables for server owners/mods
    * Custom prefix
    * Custom SizeBot role and SizeBot User role
    * Custom SizeBot channel and QotD channel
    * Turn on/off features

### New Commands

* &slowspurt (&slowspurt \<rate\> \<interval\>)
* &statsnsfw \<user\>
* &statssuchthat \[attribute\] \[size\]
    * OR \[attribute\] \[otheruser/othersize\] \[otherattribute\]
    * OR \[attribute\] \[otheruser/othersize\] \[otherattribute\] \[size\]
* &statsnsfwsuchthat \[attribute\] \[size\]
    * OR \[attribute\] \[otheruser/othersize\] \[otherattribute\]
    * OR \[attribute\] \[otheruser/othersize\] \[otherattribute\] \[size\]
* &comparensfw \[user1/size1\] \<user2/size2\>
* &objectcompare \<user/size\> (&objcompare?)
* &setother \<user\> \<attribute\> \<value\>
* &changeother \<user\> \<attribute\> \<style\> \<amount\>
* &whitelist/blacklist \[on/off, add/remove\] \<users...\>
* &autorole \[on/off\]
* &card \<user\>
* &schedule \[date/time\] \[command...\]
* &sudo \[user\] \[command...\]

## DigiFormatter

* Split into separate files for different groups of functions.
* Define its purpose.
* Can you generate . functions dynamically?
    * The user creates a custom style
    * They can then call it with `digiformatter.`\[stylename\]`(string)`
