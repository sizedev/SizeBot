# Styling Rules
***Let's keep this consistent.***

### Indents
Indents should be four spaces per level, a.k.a. "soft tabs."

### Functions and Classes
Function names should be in camelCase. (`myFunction()`)<br>
Cogs should be in PascalCase. (`class MyCog(commands.Cog)`)<br>
Commands have to be in lowercase. (`async def mycommand(self, ctx)`)

Apparently, there should be two blank lines between these things.<a href="#footnote1"><sup>1</sup></a>

### Variables

Variables should be all lowercase, with underscores (`_`) if desired.

### "Magic Number" Constants

Usually used for indexes you want to be able to understand at a glance. I prefer these to be four characters in all uppercase. (`INDX = 1`)<a href="#footnote2"><sup>2</sup></a>

### Formatting strings

Use f-strings. Just do it.    
`f"This is a pretty {swearword} cool string."`

### Comments
Comments should start have a space between the hash and the comment.<a href="#footnote1"><sup>1</sup></a>    
TODO comments should start with `# TODO:`.

____

<small>
<a name="footnote1"></a><sup>1</sup> Natalie has recommended this, and she's a real programmer.    
<a name="footnote2"></a><sup>2</sup> This isn't a standard formatting thing, it just makes me understand what the variable means better.
