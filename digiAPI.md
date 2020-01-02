# DigiAPI
**I'm very inventive.**
__________
## Terms

A `Quantity` is a dUnit construct that has a value and a unit attached. In human terms, "2 meters", for example.

A `Unit` is a dUnit thing that's a class with a name for the unit, a symbol, a factor, and a "trigger point".

* A trigger point is at what factor should we switch to using this unit. It's usually the same as the factor but not always.


## dUnit
dUnits are magical things Natalie will invent. They are basically value/unit pairs with more features.

`Quantity.getBestUnit(unitlist)`
* Called on a Quantity, give it a Unit list and picks the best one based on trigger point.

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

`createTask(executor, input)`<sup>?</sup>
* Create a repeating or scheduled command.
