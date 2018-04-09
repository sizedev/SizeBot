def toCV(size):
    size = size.upper()
    if size == "AA" or size == "AAA":
        return "0.5"
    firstlet = str(ord(size[0])&31)
    extraletters = len(size) - 1
    return str(int(firstlet) + extraletters)

def fromCV(value):
    if value == "0.5":
        return "AA"
    elif int(value) > 0.5 and int(value) <= 26:
        return chr(int(value) + 64)
    elif int(value) > 26:
        return "Z" * (int(value) - 25)

test1 = "AA"
test2 = "C"
test3 = "DD"
test4 = "J"
test5 = "Z"
test6 = "ZZZ"

print(test1)
print(toCV(test1))
print(fromCV(toCV(test1)))
print(test2)
print(toCV(test2))
print(fromCV(toCV(test2)))
print(test3)
print(toCV(test3))
print(fromCV(toCV(test3)))
print(test4)
print(toCV(test4))
print(fromCV(toCV(test4)))
print(test5)
print(toCV(test5))
print(fromCV(toCV(test5)))
print(test6)
print(toCV(test6))
print(fromCV(toCV(test6)))