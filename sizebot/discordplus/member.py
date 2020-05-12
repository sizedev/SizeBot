from discord import Member

# List of roles that map to each gender
gender_roles = {
    "m": ["male", "boy", "man", "masculine", "ftm"],
    "f": ["female", "girl", "woman", "feminine", "mtf"],
    "x": ["non-binary", "nonbinary"]
}
# Add "trans " prefix alterative for each role
for gender, roles in gender_roles.items():
    # Iterate over tuple(roles) so that we append to the same list we are iterating
    for role in tuple(roles):
        roles.append("trans " + role)

# List of roles that map to each pronoun
pronoun_roles = {
    "he": ["he/his", "he"],
    "she": ["she/her", "she"],
    "they": ["they/them", "they"]
}

# Map each gender to a pronoun
gender_to_pronoun = {
    "m": "he",
    "f": "she",
    "x": "they",
}

# Map each pronoun to a gender
pronoun_to_gender = {
    "he": "m",
    "she": "f",
    "they": "x"
}


@property
def rolelist(self):
    return [role.name for role in self.roles]


def get_genders(roles):
    genders = []
    for gender, roles_list in gender_roles.items():
        if any(role.name.lower() in roles_list for role in roles):
            genders.append(gender)
    return genders


def get_pronouns(roles):
    pronouns = []
    for pronoun, roles_list in pronoun_roles.items():
        if any(role.name.lower() in roles_list for role in roles):
            pronouns.append(pronoun)
    return pronouns


@property
def gender(self):
    genders = get_genders(self.roles)

    # One gender found
    if len(genders) == 1:
        gender = genders[0]
        # We don't support non-binary gender, yet.
        if gender == "x":
            gender = None
        return gender

    # Multiple genders found, result is ambigious
    if len(genders) > 1:
        return None

    # No genders found, fallback to pronouns
    pronouns = get_pronouns(self.roles)
    # One pronoun found
    if len(pronouns) == 1:
        gender = pronoun_to_gender[pronouns[0]]
        # We don't support non-binary gender, yet.
        if gender == "x":
            gender = None
        return gender

    # No genders found, and either ambigious or no pronouns found
    return None


@property
def pronouns(self):
    pronouns = get_pronouns(self.roles)

    # One pronoun found
    if len(pronouns) == 1:
        pronoun = pronouns[0]
        return pronoun

    # Multiple pronouns found, result is ambigious
    if len(pronouns) > 1:
        return None

    # No pronouns found, fallback to gender
    genders = get_genders(self.roles)
    # One gender found
    if len(genders) == 1:
        pronoun = gender_to_pronoun[genders[0]]
        return pronoun

    # No pronouns found, and either ambigious or no genders found
    return None


def patch():
    Member.rolelist = rolelist
    Member.gender = gender
    Member.pronouns = pronouns
