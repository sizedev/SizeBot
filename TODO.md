## SizeBot 3.7
* All text into embeds (dialog function?)
* BetterStats
    - &simplestats
    - &comparestat
    - Hide irrelevant stats
* Fix &start, &sofar
* Clean up object comparisons
    - make &objs a menu
    - &categories
    - Better output on compare
* Triggers
    - enable/disable people viewing your triggers
    - case sensitive/non-sensitive
    - self-only triggers
* Multi-unit sizetags
* Multiguild invite request
* Clothing size
* Standardize embeds
* &throw
* add yards as a valid input (not output) unit
* fake users for when you compare with a celebrity or a character<sup>?</sup> | #187


## SizeBot4

* Slash commands for basic functionality
* Custom advanced command parser
    - Pipes
    - Multiline
    - Dash-flags
        - verbosity, unit system, text/embed, rp/realistic equations, etc | #159, #114
    - Keyword arguments
* Sizekick (dice and math module with size)
* Custom stats
* Achievements | #131
* SizeTie: tie sizes to external numbers, like Twitter followers, etc. | #177
* Guild sync | #128
* Custom slowchange curves | #71
* SizeScript (a scripting language for advanced math) 
* Real database
* Switchable user profiles (create characters, switch between them)<sup>?</sup>
* Replace digiSV with dunit
* Custom emojis trigger events
* Generate user "cards"
* Auto-role based on current size option (optional for user)
* Allow users to change other users (on, blacklist, whitelist, off)
* More customizables
* Natural language chat/help (like a virtual assistant) \[needs a name\]
* Per-guild customizables for server owners/mods
    * Custom SizeBot role and SizeBot User role
    * Custom SizeBot channel and QotD channel
    * Turn on/off features
* Basic English syntax for some commands.<sup>?</sup>
* Question of the Day
    * Users can submit questions
    * These get posted to a voting channel for mods only.
    * Mods react to the submissions with emotes (:voteyes:/:voteno:)
    * If it gets accepted, it gets added to the pool.
    * A random question (with credit) is posted to a question of the day channel every morning.

### New Commands

* &convert (\<size\> \<new unit\>)
* &slowspurt (&slowspurt \<rate\> \<interval\>)
* &statssuchthat \[attribute\] \[size\]
    * OR \[attribute\] \[otheruser/othersize\] \[otherattribute\]
    * OR \[attribute\] \[otheruser/othersize\] \[otherattribute\] \[size\]
* &setother \<user\> \<attribute\> \<value\>
* &changeother \<user\> \<attribute\> \<style\> \<amount\>
* &whitelist/blacklist \[on/off, add/remove\] \<users...\>
* &card \<user\>
* &schedule \[date/time\] \[command...\]