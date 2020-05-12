from discord import Member


@property
def gender(self):
    return None


@property
def pronoun(self):
    return None


def patch():
    Member.gender = gender
    Member.pronoun = pronoun
