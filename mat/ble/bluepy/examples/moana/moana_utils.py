def strToInt(string):
    # convert a string to an integer
    v = 0
    i = 0
    for c in string:
        v |= ord(c) << i
        i += 8
    return v
