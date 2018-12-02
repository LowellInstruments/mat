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


def convert_coordinate(axis, coord_str, direction):
    LAT_LON_SPEC = {'lat': (2, 'N'), 'lon': (3, 'E')}
    split, positive = LAT_LON_SPEC[axis]
    degrees = coord_str[:split]
    minutes = coord_str[split:]
    decimal = float(degrees) + float(minutes)/60
    if direction == positive:
        return decimal
    return -decimal


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
        self.measures = {}
        if self.rmc and self.rmc.get("longitude"):
            lon = convert_coordinate("lon", str(self.rmc["longitude"]), "W")
            lon = str("{0:.4f}".format(lon))
            lat = convert_coordinate("lat", str(self.rmc["latitude"]), "N")
            lat = str("{0:.4f}".format(lat))
            self.measures["rmc_longitude"] = lon
            self.measures["rmc_latitude"] = lat
            self.measures["rmc_timestamp"] = str(self.rmc["timestamp"])
        return self.measures
