import time
import serial
import datetime


PORT_CTRL = '/dev/ttyUSB2'
PORT_DATA = '/dev/ttyUSB1'


def gps_parse_rmc_frame(data):
    s = data.split(",")
    if s[2] == 'V':
        print('not enough info')
        return

    _t = s[1][0:2] + ":" + s[1][2:4] + ":" + s[1][4:6]
    _day = s[9][0:2] + "/" + s[9][2:4] + "/" + s[9][4:6]

    # lat, direction, lon, direction, speed, course, variation
    lat = _coord_decode(s[3])
    dir_lat = s[4]
    lon = _coord_decode(s[5])
    dir_lon = s[6]
    speed = s[7]
    _course = s[8]
    variation = s[10]

    # GPS date and time are UTC
    fmt = '{} {}'.format(_day, _t)
    gps_time = datetime.datetime.strptime(fmt, '%d/%m/%y %H:%M:%S')

    # display
    print('time {} date {} lat {} lon {}'.format(_t, _day, lat, lon))
    print('speed {} mag_var {} course {}'.format(speed, variation, _course))

    # return some strings
    lat = lat * 1 if dir_lat == 'N' else lat * -1
    lon = lon * 1 if dir_lon == 'E' else lon * -1

    # checksum skipping initial '$'
    cs_in = data.split('*')[1]
    cs_calc = 0
    for c in data[1:].split('*')[0]:
        cs_calc ^= ord(c)
    cs_calc = hex(cs_calc)[-2:]
    if cs_calc != cs_in:
        return None

    # everything went ok
    return lat, lon, gps_time


def _coord_decode(coord):
    # src: stackoverflow 18442158 latitude format
    x = coord.split(".")
    head = x[0]
    deg = head[:-2]
    minutes = '{}.{}'.format(head[-2:], x[1])
    decimal = int(deg) + float(minutes) / 60
    return decimal


def enable_gps_quectel_output() -> int:
    rv = 0
    sp = serial.Serial(PORT_CTRL, baudrate=115200, timeout=0.5)
    try:
        # ensure GPS disabled, try to enable it
        sp.write(b'AT+QGPSEND\r')
        sp.write(b'AT+QGPSEND\r')
        sp.write(b'AT+QGPS=1\r')
        # ignore echo
        sp.readline()
        ans = sp.readline()
        rv = 0 if ans == b'OK\r\n' else 2
        # errors: 504 (already on), 505 (not activated)
        if ans.startswith(b'+CME ERROR: '):
            print(ans)
            rv = ans.decode()[-3]
    except (FileNotFoundError, Exception) as ex:
        print(ex)
        rv = 1
    finally:
        if sp:
            sp.close()
        return rv


# for testing purposes
def loop():
    rv = enable_gps_quectel_output()
    if rv == 0:
        print('GPS Quectel receiving...')
        sp = serial.Serial(PORT_DATA, baudrate=115200, timeout=0.5)
        while True:
            data = sp.readline()
            if data and b'$GPRMC' in data:
                gps_parse_rmc_frame(data)
    else:
        print('GPS output could not be enabled')
