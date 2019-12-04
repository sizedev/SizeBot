import os
import math
from time import strftime, localtime

from colored import fore, back, style, fg, bg, attr

#Activate VT-100 terminal formatting.
os.system("")

#Constants.
FORE = 0
BACK = 1
ATTR = 2
version = "0.3.2"

#Customizables.
timecolor = 5
msgcolor = 51
testcolor = 4
linelength = 100
timestring = "%d %b %H:%M:%S"

#Customizable color presets.
customs = {}

#ASCII/ANSI characters.
BLANK = ' '
TWENTYFIVE = '\u2591'
FIFTY = '\u2592'
SEVENTYFIVE = '\u2593'
FULL = '\u2588'
BELL = BEL = '\x07'

#VT-100 escape sequences.
ESC = '\033'

CURSOR_UP = C_UP = ESC + 'A'
CURSOR_DOWN = C_DOWN = ESC + 'B'
CURSOR_RIGHT = C_RIGHT = ESC + 'C'
CURSOR_LEFT = C_LEFT = ESC + 'D'
CURSOR_HOME = C_HOME = ESC + 'H'

SAVE_CURSOR = C_SAVE = ESC + '7'
LOAD_CURSOR = C_LOAD = ESC + '8'

START_CURSOR_BLINKING = C_BLINK_ON = ESC + '[?12h'
STOP_CURSOR_BLINKING = C_BLINK_OFF = ESC + '[?12l'
SHOW_CURSOR = C_SHOW = ESC + '[?25h'
HIDE_CURSOR = C_HIDE = ESC + '[?25l'

SCROLL_UP = ESC + '[1S'
SCROLL_DOWN = ESC + '[1S'

INSERT_BLANK = INS_BLANK = ESC + "[1@"
DELETE_CHAR = DEL_CHAR = ESC + "[1P"
ERASE_CHAR = ERS_CHAR = ESC + "[1X"
INSERT_LINE = INS_LINE = ESC + "[1L"
DELETE_LINE = DEL_CHAR = ESC + "[1M"

CLEAR_LINE_FROM_CURSOR_RIGHT = CLEAR_RIGHT = ESC + "[0K"
CLEAR_LINE_FROM_CURSOR_LEFT = CLEAR_LEFT = ESC + "[1K"

CLEAR_SCREEN_FROM_CURSOR_DOWN = CLEAR_DOWN = ESC + "[0J"
CLEAR_SCREEN_FROM_CURSOR_UP = CLEAR_UP = ESC + "[1J"

CLEAR_SCREEN = CLEAR = CLS = ESC + "[2J"

END_OF_LINE = EOL = CURSOR_RIGHT * linelength
BEGIN_OF_LINE = BOL = CURSOR_LEFT * linelength

RESET_TERMINAL = RESET = ESC + 'c'

#Cursor movement functions.
def cursorUp(amount):
    print(ESC + f"[{amount}A")
def cursorDown(amount):
    print(ESC + f"[{amount}B")
def cursorRight(amount):
    print(ESC + f"[{amount}C")
def cursorLeft(amount):
    print(ESC + f"[{amount}D")

#Scrolling methods.
def scrollUp(amount):
    print(ESC + f'[{amount}S')
def scrollDown(amount):
    print(ESC + f'[{amount}T')

#Set window title.
def setWindowTitle(string):
    print(ESC + f"2;{string}{BELL}")

#Delete an amount of lines.
def overwriteLines(lines):
    return BeginOfLine + ((CursorUp + DeleteLine) * lines)

#Set methods for customizables.
def settimecolor(new):
    global timecolor
    timecolor = new
def setmsgcolor(new):
    global msgcolor
    msgcolor = new
def settestcolor(new):
    global testcolor
    testcolor = new
def setlinelength(new):
    global linelength
    linelength = new
def settimestring(new):
    global timestring
    timestring = new

#Color styling for terminal messages.
def time():
    return (fg(timecolor) + strftime(f"{timestring} | ", localtime()) + style.RESET)
def warn(message, showtime = True):
    if showtime: print (time() + fore.YELLOW + message + style.RESET)
    else: print (fore.YELLOW + message + style.RESET)
def crit(message, showtime = True):
    if showtime: print (time() + back.RED + style.BOLD + message + style.RESET)
    else: print (back.RED + style.BOLD + message + style.RESET)
def test(message, showtime = True):
    if showtime: print (time() + fg(testcolor) + message + style.RESET)
    else: print (fg(testcolor) + message + style.RESET)
def load(message, showtime = False):
    if showtime: print (time() + fg(238) + message + style.RESET)
    else: print (fg(238) + message + style.RESET)
def msg(message, showtime = True):
    if showtime: print (time() + fg(msgcolor) + message + style.RESET)
    else: print (fg(msgcolor) + message + style.RESET)

#Create a custom color preset.
def createCustom(name, fore = 256, back = 256, attr = None):
    global customs
    customs[name] = [fore, back, style]

#Use a custom color preset.
def custom(name, message, showtime = True):
    fgcolor = customs[name][FORE]
    bgcolor = customs[name][BACK]
    attr = customs[name][ATTR]
    if attr is not None:
        if showtime: print (time() + fg(fgcolor) + bg(bgcolor) + message + style.RESET)
        else: print (fg(fgcolor) + bg(bgcolor) + message + style.RESET)
    else:
        if showtime: print (time() + fg(fcolor) + bg(bgcolor) + attr(attr) + message + style.RESET)
        else: print (fg(fcolor) + bg(bgcolor) + attr(attr) + message + style.RESET)

#Create a progress bar.
def createLoadBar(current, total, barlength = 50, showpercent = False):
    progress = ((current/total)*100)
    bar = ""
    percentage = progress
    progress *= (barlength * 4 / 100)
    progress = int(progress)
    bars = math.floor(progress/4)
    bar = FULL * bars
    shade = progress - (bars*4)
    if shade == 1: bar += TWENTYFIVE
    if shade == 2: bar += FIFTY
    if shade == 3: bar += SEVENTYFIVE
    printableperc = round(((current/total)*100), 2)
    returnstring = bar
    if showpercent: returnstring = f"{returnstring} {printableperc}%"
    return returnstring

#Truncate a long string for terminal printing.
def truncate(item, trunclen = 80):
    if len(item) > trunclen:
        printitem = "…" + item[-(trunclen - 1):]
    else:
        printitem = item
    return printitem
