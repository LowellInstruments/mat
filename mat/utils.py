import glob
import platform
import re
import shlex
from numpy import array, mod
from datetime import datetime
import numpy as np
import os
import subprocess as sp


def obj_from_coefficients(coefficients, classes):
    coefficient_set = set(coefficients)
    for klass in classes:
        keys = klass.REQUIRED_KEYS
        if keys <= coefficient_set:
            return klass(coefficients)
    return None


def trim_start(string, n_chars_to_trim):
    return string[n_chars_to_trim:]


def array_from_tags(data, *key_lists):
    return array([[data[key] for key in key_list]
                  for key_list in key_lists])


def cut_out(string, start_cut, end_cut):
    return string[:start_cut] + string[end_cut:]


def epoch(time):
    return (time - datetime(1970, 1, 1)).total_seconds()


def epoch_from_timestamp(date_string):
    """ Return posix timestamp """
    epoch_time = datetime(1970, 1, 1)
    date_time = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
    return (date_time - epoch_time).total_seconds()


def parse_tags(string):
    """
    Break a string of tag/value pairs separated by \r\n into a dictionary
    with tags as keys
    eg
    parse_tags('ABC 123\r\nDEF 456\r\n')
    would return
    {'ABC': '123', 'DEF': '456'}
    """
    lines = string.split('\r\n')[:-1]
    dictionary = {}
    for tag_and_value in lines:
        tag, value = tag_and_value.strip().split(' ', 1)
        dictionary[tag] = value
    return dictionary


def four_byte_int(b: bytes, signed=False):
    try:
        if len(b) != 4:
            return 0
        result = int(b[2:4] + b[0:2], 16)
        if signed and result > 32768:
            return result - 65536
        return result
    except ValueError:
        raise RuntimeError("Unable to extract integer from %s" % b)


def roll_pitch_yaw(accel, mag):
    """
    Convert accel and mag components into yaw/pitch/roll. Output is in radians
    """
    roll = np.arctan2(accel[1], accel[2])
    pitch = np.arctan2(-accel[0],
                       accel[1] * np.sin(roll) + accel[2] * np.cos(roll))
    by = mag[2] * np.sin(roll) - mag[1] * np.cos(roll)
    bx = (mag[0] * np.cos(pitch) + mag[1] * np.sin(pitch) * np.sin(roll)
          + mag[2] * np.sin(pitch) * np.cos(roll))
    yaw = np.arctan2(by, bx)
    return roll, pitch, yaw


def apply_declination(heading, declination):
    return mod(heading + 180 + declination, 360) - 180


class PrintColors:
    # ex: print(p_c.OKGREEN + "hello" + p_c.ENDC)
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def G(s):
        print(PrintColors.OKGREEN + s + PrintColors.ENDC)

    @staticmethod
    def B(s):
        print(PrintColors.OKBLUE + s + PrintColors.ENDC)

    @staticmethod
    def Y(s):
        print(PrintColors.WARNING + s + PrintColors.ENDC)

    @staticmethod
    def R(s):
        print(PrintColors.FAIL + s + PrintColors.ENDC)

    @staticmethod
    def N(s):
        print(s)


def linux_is_rpi():
    if platform.system() == 'Windows':
        return False
    # better than checking architecture
    return os.uname().nodename in ('raspberrypi', 'rpi', 'raspberry')


def linux_is_rpi3():
    c = 'cat /proc/cpuinfo'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return b'Raspberry Pi 3' in rv.stdout


def linux_is_rpi4():
    c = 'cat /proc/cpuinfo'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return b'Raspberry Pi 4' in rv.stdout


def linux_set_datetime(s) -> bool:
    # requires root or $ setcap CAP_SYS_TIME+ep /bin/date
    # w/ NTP enabled, time gets re-set very fast so,
    # when testing, just go offline

    s = 'date -s "{}"'.format(s)
    o = sp.DEVNULL
    rv = sp.run(shlex.split(s), stdout=o, stderr=o)
    return rv.returncode == 0


def is_valid_mac_address(mac):

    if mac is None:
        return False

    # src: geeks for geeks website
    regex = ("^([0-9A-Fa-f]{2}[:])" +
             "{5}([0-9A-Fa-f]{2})|" +
             "([0-9a-fA-F]{4}\\." +
             "[0-9a-fA-F]{4}\\." +
             "[0-9a-fA-F]{4})$")
    return re.search(re.compile(regex), mac)


def lowell_cmd_dir_ans_to_dict(ls, ext, match=True):
    if ls is None:
        return {}

    if b'ERR' in ls:
        return b'ERR'

    if type(ext) is str:
        ext = ext.encode()

    files, idx = {}, 0

    # ls: b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r\n\rMAT.cfg\t\t\t189\n\r\x04\n\r'
    ls = ls.replace(b'System Volume Information\t\t\t0\n\r', b'')
    ls = ls.split()

    while idx < len(ls):
        name = ls[idx]
        if name in [b'\x04']:
            break

        names_to_omit = (
            b'.',
            b'..',
        )

        if type(ext) is str:
            ext = ext.encode()
        # wild-card case
        if ext == b'*' and name not in names_to_omit:
            files[name.decode()] = int(ls[idx + 1])
        # specific extension case
        elif name.endswith(ext) == match and name not in names_to_omit:
            files[name.decode()] = int(ls[idx + 1])
        idx += 2
    return files


def write_sws_file(path, data):
    # the data are in int16 format. Convert back to 8 bit ascii values
    data.dtype = np.uint8

    # strip any nulls, etc.
    sws = ''.join([chr(x) for x in data if chr(x).isprintable()])

    with open(path, 'w') as f:
        f.write('SWS: ' + sws)


def consecutive_numbers(data, number, count):
    c = 0
    for i, val in enumerate(data):
        if val == number:
            c += 1
        else:
            c = 0
        if c == count:
            return i-count+1
    return len(data)


def linux_ls_by_ext(fol, extension):
    """ recursively collect all logger files w/ indicated extension """

    if not fol:
        return []
    if os.path.isdir(fol):
        wildcard = fol + '/**/*.' + extension
        return glob.glob(wildcard, recursive=True)
