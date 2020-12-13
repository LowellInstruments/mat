import time
import serial


PORT_CTRL = '/dev/ttyUSB2'
PORT_DATA = '/dev/ttyUSB1'


def gps_parse_rmc_frame(data):
    s = data.split(",")
    if s[2] == 'V':
        print('not enough info')
        return

    _t = s[1][0:2] + ":" + s[1][2:4] + ":" + s[1][4:6]
    date = s[9][0:2] + "/" + s[9][2:4] + "/" + s[9][4:6]
    # lat, direction, lon, direction, speed, course, variation
    lat = decode(s[3])
    dirLat = s[4]
    lon = decode(s[5])
    dirLon = s[6]
    speed = s[7]
    _course = s[8]
    variation = s[10]

    # checksum
    dc = s[11].split("*")
    degree = dc[0]        #degree
    checksum = dc[1]      #checksum

    # display
    print('time {} lat {} lon {} checksum {}'.format(_t, lat, lon, checksum))
    print('speed {} mag_var {} course {}'.format(speed, variation, _course))


def decode(coord):
    # DDDMM.MMMMM -> DD deg MM.MMMMM min
    x = coord.split(".")
    head = x[0]
    tail = x[1]
    deg = head[0:-2]
    min = head[-2:]
    return deg + " deg " + min + "." + tail + " min"


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


if __name__ == '__main__':
    loop()
