# defines constant labels, as strings, used for displaying and tracking the types of tiles

FIND_OUT  = '*'
BLANK     = '-'
EMPTY     = '.'
DIGIT_1   = '1'
DIGIT_2   = '2'
DIGIT_3   = '3'
DIGIT_4   = '4'
DIGIT_5   = '5'
DIGIT_6   = '6'
DIGIT_7   = '7'
DIGIT_8   = '8'
FLAG      = 'F'
EXPLODED  = 'B'
_UNKNOWN = {FIND_OUT, BLANK}
_DIGITS = {DIGIT_1, DIGIT_2, DIGIT_3, DIGIT_4, DIGIT_5, DIGIT_6, DIGIT_7, DIGIT_8}

def is_find_out(lbl: str) -> bool:
    return lbl == FIND_OUT
def is_blank(lbl: str) -> bool:
    return lbl == BLANK
def is_unknown(lbl: str) -> bool:
    return lbl in _UNKNOWN
def is_empty(lbl: str) -> bool:
    return lbl == EMPTY
def is_digit(lbl: str) -> bool:
    return lbl in _DIGITS
def is_flag(lbl: str) -> bool:
    return lbl == FLAG
def is_exploded(lbl: str) -> bool:
    return lbl == EXPLODED

def digit_of(lbl: str) -> int:
    digit = int(lbl)
    if(8 < digit or digit < 0): raise ValueError("lbl was a number ({}) but not within the range 0 to 8".format(digit))
    return digit