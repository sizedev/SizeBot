* ~~Don't import * globalsb~~
* ~~Clean up all the imports really~~
* ~~Follow and document style conventions~~
* ~~Prevent that error we keep getting on readuser~~
* Setup develop branch
* Host Sizebot Unstable on VPS
    * Setup automatic deployment of develop branch commits
* Migrate to MariaDB
    * Make repeating tasks check the database every X time instead of asyncio tasks that are unwieldy
    * Guilds
    * Members
    * "Characters"
    * Winks
* Migrate legacy User constants to new User object
* Formatting
    * Replace .format() with f-strings
    * Fix allowbrackets
    * Fix flake8 linting to check for more issues
* Fix Unicode handling for nicknames (if this is even possible)
* Make a custom emoji dictionary
* Add support for multiple guilds
* Commands
    * Make register commands easier to use and give better use output (simpler usage and better defaults)
    * Change the way &slowchange works (&slowchange \<rate\> \<stopcondition\>)
    * Create convert command (&convert \<size\> \<new unit\>)
    * Custom base height/weight for raw compares
    * Create eval commad (for devs only)
* Switch some things to embeds
* Make SizeBot respond to DMs in a helpful way
* Separate command logic into modules
    * Register commands
    * Size change commands
    * Size comparison commands
* Setup testing
    * Register commands
    * Size change command
    * Size comparison commands
    * Dice rolling
    * Size conversion
* Replace digiSV with dunit
