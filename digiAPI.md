# DigiAPI
**I'm very inventive.**
__________
## dUnit
dUnits are magical things Natalie will invent. They are basically value/unit pairs with more features.

## User
getUser(id)
* Tries to get a SizeBot User from their Discord ID. Returns `None`<sup>?</sup> if it can't.

`User.[height, baseheight, baseweight...]`
* Get that attribute.

`User.[setHeight, setBaseHeight, setBaseWeight](dUnit)`
* Set an attribute.

## Functions

`buildStats(User or dUnit, list)`
* Creates a user-readable output of stats based on the list of desired stats in the list.
* e.g.: `buildStats(getUser(ID), [stats.height, stats.weight, stats.footlength])` would produce:
```
Stats for **Fake Person**:
Height: 2m | 6'6"
Weight: 90kg | ???lb
Foot Length: 0.3m | 1ft (Shoe Size: US ???)
```

`buildCompare(User or dUnit, User or dUnit, list)`
* See above.

`createTask(executor, input)`
* Create a repeating or scheduled command.
