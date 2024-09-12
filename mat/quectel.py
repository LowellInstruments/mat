#!/usr/bin/env python3


import os
import serial
import time


SERIAL_RATE = 115200
FILE_QUECTEL_USB_GPS = '/tmp/usb_quectel_gps'
FILE_QUECTEL_USB_CTL = '/tmp/usb_quectel_ctl'


def detect_quectel_usb_ports():
    for i in (FILE_QUECTEL_USB_GPS, FILE_QUECTEL_USB_CTL):
        if os.path.exists(i):
            os.unlink(i)
    found_gps = ''
    found_ctl = ''
    for i in range(5):
        p = f'/dev/ttyUSB{i}'
        till = time.perf_counter() + 1
        b = bytes()
        ser = None
        try:
            ser = serial.Serial(p, SERIAL_RATE, timeout=.1, rtscts=True, dsrdtr=True)
            ser.write(b'AT+QGPS=1 \rAT+QGPS=1 \r')
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
            print('b', b)
            if found_gps and found_ctl:
                break
        except (Exception,) as ex:
            if ser and ser.isOpen():
                ser.close()
            # print(f'error {p} -> {ex}')
    with open(FILE_QUECTEL_USB_GPS, 'w') as f:
        f.write(found_gps)
    with open(FILE_QUECTEL_USB_CTL, 'w') as f:
        f.write(found_ctl)
    return found_gps, found_ctl


if __name__ == '__main__':
    rv = detect_quectel_usb_ports()
    print('rv', rv)
