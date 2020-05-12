from discord import Member

genderrolemap = {
    "male":      "m",
    "boy":       "m",
    "man":       "m",
    "masculine": "m",
    "female":    "f",
    "girl":      "f",
    "woman":     "f",
    "feminine":  "f"
}

pronounrolemap = {
    "he/his":    "he",
    "she/her":   "she",
    "they/them": "they"
}


@property
def rolelist(self):
    return [role.name for role in self.roles]


@property
def gender(self):
    foundmale = False
    foundfemale = False

    for role in self.rolelist:
        role = role.lower()
        if role.startswith("trans "):
            role = role[6:]
        if genderrolemap[role] == "m":
            foundmale = True
        elif genderrolemap[role] == "f":
            foundfemale = True

    if not foundmale and not foundfemale:
        if self.pronoun == "he":
            foundmale = True
        if self.pronoun == "she":
            foundfemale = True

    if not foundmale ^ foundfemale:
        return None
    if foundmale:
        return "m"
    if foundfemale:
        return "f"


@property
def pronoun(self):
    foundhe = False
    foundshe = False
    foundthey = False

    for role in self.rolelist:
        if pronounrolemap[role] == "he":
            foundhe = True
        elif pronounrolemap[role] == "she":
            foundshe = True
        elif pronounrolemap[role] == "they":
            foundthey = True

    if not foundhe and not foundshe and not foundthey:
        if self.gender == "m":
            foundhe = True
        if self.gender == "f":
            foundshe = True

    if not foundhe ^ foundshe ^ foundthey:
        return None
    if foundhe:
        return "he"
    if foundshe:
        return "she"
    if foundthey:
        return "they"


def patch():
    Member.rolelist = rolelist
    Member.gender = gender
    Member.pronoun = pronoun
