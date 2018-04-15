import os
from pathlib import Path
from globalsb import *

#Eat the file and spit it somewhere else for the future.
path = folder + '/users'
listing = os.listdir(path)
for infile in listing:
    with open(infile) as f:
        #Make array of lines from file.
        content = f.readlines()
        #Replace None.
        if content[BWEI] == "None" + newline:
            content[BWEI] = str(defaultweight) + newline
        if content[BHEI] == "None" + newline:
            content[BHEI] = str(defaultweight) + newline
        if content[CHEI] == "None" + newline:
            content[CHEI] = content[3]
        #Round all values to 18 decimal places.
        content[CHEI] = str(round(float(content[CHEI]), 18))
        content[BHEI] = str(round(float(content[BHEI]), 18))
        content[BWEI] = str(round(float(content[BWEI]), 18))
        for idx, item in enumerate(content):
            if not content[idx].endswith("\n"):
                content[idx] = content[idx] + "\n"
        os.remove(folder + "/users/" + user_id + ".txt")
        #Make a new userfile.
        userfile = open(folder + "/users/" + user_id + "/main.txt", "w+")
        #Write content to lines.
        userfile.writelines(content)
