import serial
import datetime

BAUD_RATE = 4800


def to_decimal_degrees(value, nsew):
    # RMC example: 4807.038,N (DM.m) == Latitude 48 deg 07.038' N
    if not value:
        return None
    a, b = value.split('.')
    degrees = int(a) // 100
    minutes = int(a) % 100
    minutes += float(int(b) / 10 ** len(b))
    result = degrees + minutes / 60.0
    if nsew in 'SW':
        result = -result
    return result


def parse_int(x):
    return int(x) if x else None


def parse_float(x):
    return float(x) if x else None


# Device Object
class GPS:

    def __init__(self, port, baud_rate=BAUD_RATE):
        self.port = serial.Serial(port, baud_rate)
        self.handlers = {
            '$GPRMC': self.on_rmc,
        }
        self.rmc = None

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
            # sent to parsers, aka handlers, aka "on_*"
            if handler and tokens[1] != "":
                handler(args)
                return True
        return False

    def on_rmc(self, args):
        valid = args[1] == 'A'
        timestamp = datetime.datetime.strptime(args[8] + args[0],
                                               '%d%m%y%H%M%S.%f')
        latitude = to_decimal_degrees(args[2], args[3])
        longitude = to_decimal_degrees(args[4], args[5])
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

    def get_last_rmc_frame(self):
        rmc_frame = {}
        if self.rmc and self.rmc.get("timestamp"):
            rmc_frame["rmc_longitude"] = str(self.rmc["longitude"])
            rmc_frame["rmc_latitude"] = str(self.rmc["latitude"])
            rmc_frame["rmc_timestamp"] = str(self.rmc["timestamp"])
        return rmc_frame
