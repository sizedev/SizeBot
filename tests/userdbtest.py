# TODO: Make this into a real test.

from sizebot import userdb
from sizebot.userdb import SPEC, User

userdata = User()
userdata.id = "123"
print("Created new user")
print(userdata)

userdata.nickname = "Steve"
print("Set user's nickname using new attribute")
print(userdata)

userdata[SPEC] = "Catperson"
print("Set user's nickname using deprecated array access")
print(userdata)

print("Saving user")
userdb.save(userdata)

print("Loading user by id into a new variable")
userdata2 = userdb.load("123")

print(userdata2)
