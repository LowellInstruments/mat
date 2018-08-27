# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

import serial
import serial.tools.list_ports
import re
import time
import datetime

# This is the format of the string we are parsing
# $GPGGA,125742.000,4119.6607,N,07301.3281,W,1,09,1.0,100.3,M,-34.3,M,,0000*6D

def read_serial():
    port = serial.Serial('COM6', 4800)
    s = time.time()
    while time.time() - s < 3:
        while port.inWaiting():
            in_line = port.readline().decode('IBM437')
            if not verify_string(in_line):
                continue
            if not in_line.startswith('$GPGGA'):
                continue

            fields = in_line.split(',')
            latitude = convert_lat(fields[2], fields[3])
            longitude = convert_lon(fields[4], fields[5])
            utc = convert_time(fields[1])

            print('{}, {}, {}'.format(utc, latitude, longitude))

        time.sleep(0.1)


def verify_string(string):
    """
    Confirm the correct string format and calculate checksum
    The checksum is calculated by xor'ing each byte between the $ and *
    The checksum is the two digit value after the * (and is in hex)
    """
    regexp = re.search('^\$(GP[A-Z]{3}.+)\*([0-9A-F]{2})', string)
    if not regexp:
        return False
    checksum = int(regexp.group(2), 16)
    int_values = [ord(x) for x in regexp.group(1)]
    value = 0
    for x in int_values:
        value = value ^ x
    return True if value == checksum else False


def convert_lat(lat_str, ns):
    latitude = float(lat_str[0:2]) + float(lat_str[2:9])/60
    latitude = -latitude if ns == 'S' else latitude
    return latitude


def convert_lon(lon_str, ew):
    longitude = float(lon_str[0:3]) + float(lon_str[3:10])/60
    longitude = -longitude if ew == 'W' else longitude
    return longitude


def convert_time(time_str):
    time_struct = time.strptime(time_str, '%H%M%S.%f')
    return '{:0>2d}:{:0>2d}:{:0>2d}'.format(time_struct.tm_hour, time_struct.tm_min, time_struct.tm_sec)


if __name__ == '__main__':
    read_serial()
