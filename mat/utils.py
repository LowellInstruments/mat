import pathlib
import socket
from platform import machine
import crc16
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


def xmd_frame_check_crc(lc):
    data = lc.dlg.x_buf[3:-2]
    rx_crc = lc.dlg.x_buf[-2:]
    calc_crc_int = crc16.crc16xmodem(data)
    calc_crc_bytes = calc_crc_int.to_bytes(2, byteorder='big')
    return calc_crc_bytes == rx_crc


def is_service_active(name: str):
    # just name, not name.service
    s = 'systemctl is-active --quiet {}'.format(name)
    rv = sp.run(s, shell=True)
    print('service active {} ? {}'.format(name, rv.returncode == 0))
    return rv.returncode == 0


def is_service_enabled(name: str):
    # just name, not name.service
    s = 'systemctl is-enabled --quiet {}'.format(name)
    rv = sp.run(s, shell=True)
    print('service enabled {} ? {}'.format(name, rv.returncode == 0))
    return rv.returncode == 0


def show_services_running():
    # running: currently being executed, may be enabled or not
    s = 'systemctl | grep running'
    rv = sp.run(s, shell=True, stdout=sp.PIPE)
    print(rv.stdout)


def show_services_enabled():
    # enabled: will start on next boot, may be currently running or not
    s = 'systemctl list-unit-files | grep enabled'
    rv = sp.run(s, shell=True, stdout=sp.PIPE)
    print(rv.stdout)


def is_process_running_by_name(name):
    return get_pid_of_a_process(name)


def get_pid_of_a_process(name):
    # awk and so they do not work here because they use {}
    s = 'ps -aux | grep {} | grep -v grep'.format(name)
    rv = sp.run(s, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode == 0:
        pid = rv.stdout.decode().split()[1]
        return int(pid)
    return -1


def linux_is_docker():
    return pathlib.Path('/.dockerenv').is_file()


def linux_is_x64():
    return machine() == 'x86_64'


def linux_is_docker_on_x64():
    return linux_is_docker() and linux_is_x64()


def linux_is_rpi():
    # better than checking architecture
    return os.uname().nodename in ('raspberrypi', 'rpi')


def linux_is_docker_on_rpi():
    return linux_is_docker() and linux_is_rpi()
