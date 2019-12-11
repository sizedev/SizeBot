import userdb
from userdb import SPEC, User

user = User()
user.id = "123"
print("Created new user")
print(user)

user.nickname = "Steve"
print("Set user's nickname using new attribute")
print(user)

user[SPEC] = "Catperson"
print("Set user's nickname using deprecated array access")
print(user)

print("Saving user")
userdb.save(user)

print("Loading user by id into a new variable")
user2 = userdb.load("123")

print(user2)
