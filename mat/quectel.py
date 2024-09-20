#!/usr/bin/env python3


import os
import serial
import time
import subprocess as sp


VP_QUECTEL = '2c7c:0125'
VP_TELIT = '1bc7:1201'
SERIAL_RATE = 115200
# we will leave the results in these 2 files :)
FILE_QUECTEL_USB_GPS = '/tmp/usb_quectel_gps'
FILE_QUECTEL_USB_CTL = '/tmp/usb_quectel_ctl'
MAX_NUM_USB_PORTS = 5


def is_this_telit_cell():
    c = f'lsusb | grep {VP_TELIT}'
    _rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return _rv.returncode == 0


def detect_quectel_usb_ports():
    if is_this_telit_cell():
        print('no Quectel USB ports, maybe cell module Telit')
        return None, None

    for i in (FILE_QUECTEL_USB_GPS, FILE_QUECTEL_USB_CTL):
        if os.path.exists(i):
            os.unlink(i)

    found_gps = ''
    found_ctl = ''

    # iterate backwards and down to 0
    for i in range(MAX_NUM_USB_PORTS, -1, -1):
        p = f'/dev/ttyUSB{i}'
        till = time.perf_counter() + 2
        b = bytes()
        ser = None
        try:
            ser = serial.Serial(p, SERIAL_RATE, timeout=.1, rtscts=True, dsrdtr=True)
            ser.write(b'AT+QGPS=1 \rAT+QGPS=1 \r')
            time.sleep(.5)
            while time.perf_counter() < till:
                b += ser.read()
                if (b'GPGSV' in b or b'GPGSA' in b
                        or b'GPRMC' in b or b',,,,' in b):
                    found_gps = p
                    break
                if b'OK' in b or b'CME' in b:
                    found_ctl = p
                    break
            ser.close()
            if found_gps and found_ctl:
                break
        except (Exception,) as ex:
            if ser and ser.is_open:
                ser.close()
            # commented or shows 'no device in port' error
            # print(f'error Quectel USB ports -> {ex}')

    with open(FILE_QUECTEL_USB_GPS, 'w') as f:
        if found_gps:
            f.write(found_gps)
    with open(FILE_QUECTEL_USB_CTL, 'w') as f:
        if found_ctl:
            f.write(found_ctl)
    return found_gps, found_ctl


if __name__ == '__main__':
    rv = detect_quectel_usb_ports()
    print('Quectel USB ports:', rv)
