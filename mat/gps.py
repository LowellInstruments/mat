import serial
import datetime

# adapted from https://github.com/fogleman/GPS/blob/master/gps.py

# Settings
PORT = '/dev/ttyUSB0'
BAUD_RATE = 4800


def to_decimal(value, nsew):
    if not value:
        return None
    a, b = value.split('.')
    degrees = int(a) / 100
    minutes = int(a) % 100
    seconds = 60.0 * int(b) / 10 ** len(b)
    result = degrees + minutes / 60.0 + seconds / 3600.0
    if nsew in 'SW':
        result = -result
    return result


def parse_int(x):
    return int(x) if x else None


def parse_float(x):
    return float(x) if x else None


# Device Object
class GPS:
    def __init__(self, port=PORT, baud_rate=BAUD_RATE):
        self.port = serial.Serial(port, baud_rate)
        self.handlers = {
            '$GPRMC': self.on_rmc,
        }
        self.rmc = None
        self.my_measures = {}

    def read_line(self):
        while True:
            line = self.port.readline().strip()
            if line.startswith('$'.encode("ASCII")):
                return line

    def parse_line(self):
        line = self.read_line().decode("ASCII")
        if line:
            data, checksum = line.split('*')
            tokens = data.split(',')
            command, args = tokens[0], tokens[1:]
            handler = self.handlers.get(command)
            # sent to parsers
            if handler and tokens[1] != "":
                handler(args)
                return True
        return False

    def on_rmc(self, args):
        valid = args[1] == 'A'
        timestamp = datetime.datetime.strptime(args[8] + args[0],
                                               '%d%m%y%H%M%S.%f')
        latitude = to_decimal(args[2], args[3])
        longitude = to_decimal(args[4], args[5])
        knots = parse_float(args[6])
        course = parse_float(args[7])
        self.rmc = dict(
            valid=valid,
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            knots=knots,
            course=course,
        )

    def get_last_measures(self):
        self.my_measures = {}
        if self.rmc and self.rmc.get("longitude"):
            my_longitude = convert_lon(str(self.rmc["longitude"]), "W")
            my_longitude = str("{0:.4f}".format(my_longitude))
            my_latitude = convert_lat(str(self.rmc["latitude"]), "N")
            my_latitude = str("{0:.4f}".format(my_latitude))
            self.my_measures["rmc_longitude"] = my_longitude
            self.my_measures["rmc_latitude"] = my_latitude
            self.my_measures["rmc_timestamp"] = str(self.rmc["timestamp"])
        return self.my_measures


def convert_lat(lat_str, ns):
    latitude = build_latitude_from_string(lat_str)
    if ns == 'S':
        latitude = -latitude
    return latitude


def convert_lon(lon_str, ew):
    longitude = build_longitude_from_string(lon_str)
    if ew == 'W':
        longitude = -longitude
    return longitude


def build_latitude_from_string(value):
    return float(value[0:2]) + float(value[2:9]) / 60


def build_longitude_from_string(value):
    return float(value[0:3]) + float(value[3:10]) / 6
