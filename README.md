# SizeBot
SizeBot Legacy, rewritten.

[![Build Status](https://travis-ci.org/sizedev/SizeBot.svg?branch=master)](https://travis-ci.org/sizedev/SizeBot) master

[![Build Status](https://travis-ci.org/sizedev/SizeBot.svg?branch=develop)](https://travis-ci.org/sizedev/SizeBot) develop

**SizeBot** is a size-play based roleplay bot.

**SizeBot Legacy:** [SizeBot Legacy on GitHub](https://github.com/sizedev/SizeBot/tree/sizebot-legacy)

## Installation

To install the latest release of SizeBot, simply run:

`pip install git+git://github.com/SizeDev/SizeBot@master`

## Optional Requirements

If you want to host SizeBot as a systemd daemon, make sure to install the cysystemd library:

`pip install cysystemd`

# Permissions

In order to function, SizeBot requires the following basic permissions:

* View Channels
* Send Messages
* Embed Links
* Add Reactions
* Use External Emoji
* Manage Messages
* Read Message History

Add Reactions, Use External Emoji, Manage Messages, and Read Message History are all required for reaction menus to work properly.

In order to support some optional features, SizeBot may also need:

* Change Nickname
* Manage Nicknames (used to set size tags)
* Attach Files (used by various commands)
* Move Members (used by &naptime command)
* Manage Roles (used to add the SizeBot User role to users after registration)
