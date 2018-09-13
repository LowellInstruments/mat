from datetime import datetime


def parse_tags(string):
    """
    Break a string of tag/value pairs separated by \r\n into a dictionary
    with tags as keys
    eg
    parse_tags('ABC 123\r\nDEF 456\r\n')
    would return
    {'ABC': '123', 'DEF': '456}
    """
    lines = string.split('\r\n')[:-1]
    dictionary = {}
    for tag_and_value in lines:
        tag, value = tag_and_value.strip().split(' ', 1)
        dictionary[tag] = value
    return dictionary


def _trim_start(string, n_chars_to_trim):
    return string[n_chars_to_trim:]


def cut_out(string, start_cut, end_cut):
    return string[:start_cut] + string[end_cut:]


def epoch(time):
    return (time - datetime(1970, 1, 1)).total_seconds()
