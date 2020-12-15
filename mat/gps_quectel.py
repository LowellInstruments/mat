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
    dirLat = s[4]
    lon = _coord_decode(s[5])
    dirLon = s[6]
    speed = s[7]
    _course = s[8]
    variation = s[10]

    # checksum
    dc = s[11].split("*")
    degree = dc[0]
    checksum = dc[1]

    # GPS date and time are UTC
    fmt = '{} {}'.format(_day, _t)
    gps_time = datetime.datetime.strptime(fmt, '%d/%m/%y %H:%M:%S')

    # display
    print('time {} date {} lat {} lon {} checksum {}'.format(_t, _day, lat, lon, checksum))
    print('speed {} mag_var {} course {}'.format(speed, variation, _course))

    # return some strings
    lat = lat * 1 if dirLat == 'N' else lat * -1
    lon = lon * 1 if dirLon == 'E' else lon * -1

    # todo: calculate checksum
    return lat, lon, gps_time



def _coord_decode(coord):
    # src: stackoverflow 18442158 latitude format
    x = coord.split(".")
    head = x[0]
    deg = head[:-2]
    minutes = '{}.{}'.format(head[-2:], x[1])
    decimal = int(deg) + float(minutes) / 60
    return decimal


def enable_gps_output():
    print('sending AT+QGPS=1 to {}'.format(PORT_CTRL))
    sp = serial.Serial(PORT_CTRL, baudrate = 115200, timeout = 1)
    sp.write('AT+QGPS=1\r')
    sp.close()
    time.sleep(0.5)


def loop():
    enable_gps_output()
    print('GPS Quectel receiving...')
    sp = serial.Serial(PORT_DATA, baudrate = 115200, timeout = 0.5)
    while True:
        data = sp.readline()
        if '$GPRMC' in data:
            gps_parse_rmc_frame(data)



def my_test_gps_parse_rmc_frame():
    data = '$GPRMC,123519,A,07717.3644,N,01131.000,E,022.4,084.4,230394,003.1,W*6A'
    rv = gps_parse_rmc_frame(data)
    print(rv)

if __name__ == '__main__':
    my_test_gps_parse_rmc_frame()
    # loop()
