import serial
import datetime
import re
import time
from collections import namedtuple

BAUD_RATE = 4800


def parse_int(x):
    return int(x) if x else None


def parse_float(x):
    return float(x) if x else None


# Device Object
class GPS:

    RMC_Frame = namedtuple('RMC_Frame',
                           'valid timestamp latitude longitude knots course')

    def __init__(self, port, baud_rate=BAUD_RATE):
        self.port = serial.Serial(port, baud_rate)
        self.handlers = {
            '$GPRMC': self._on_rmc,
        }
        self.rmc = None

    @classmethod
    def _verify_string(cls, data, checksum):
        checksum_in_decimal = int(checksum, 16)
        print("checksum_in_decimal {}".format(checksum_in_decimal))
        int_values = [ord(x) for x in data]
        calculated = 0
        for x in int_values:
            calculated = calculated ^ x
        print("calculated {}".format(calculated))
        return True if calculated == checksum_in_decimal else False

    @classmethod
    def _to_decimal_degrees(cls, value, nsew):
        # BU-353-S4 GPS provides RMC frame as DDMM.mmmm
        if not value:
            return None
        a, b = value.split('.')
        if len(a) < 4 or len(b) < 4:
            raise ValueError
        degrees = int(a) // 100
        minutes = int(a) % 100
        minutes += float(int(b) / 10 ** len(b))
        result = degrees + minutes / 60.0
        if nsew in 'SW':
            result = -result
        return result

    def read_line(self, timeout=5):
        end_time = time.time() + timeout
        while time.time() < end_time:
            time.sleep(0.1)
            line_bytes = self.port.readline().strip()
            if line_bytes.startswith('$'.encode('ASCII')):
                line = line_bytes.decode('ASCII')
                data, checksum = line.split('*')
                tokens = data.split(',')
                command, args = tokens[0], tokens[1:]
                handler = self.handlers.get(command)
                # sent to parsers, aka handlers, aka 'on_*'
                data = data[1:]
                if GPS._verify_string(data, checksum) and handler:
                    handler(args)
                    return line
        return None

    def _on_rmc(self, args):
        valid = args[1] == 'A'
        timestamp = datetime.datetime.strptime(args[8] + args[0],
                                               '%d%m%y%H%M%S.%f')
        latitude = GPS._to_decimal_degrees(args[2], args[3])
        longitude = GPS._to_decimal_degrees(args[4], args[5])
        knots = parse_float(args[6])
        course = parse_float(args[7])
        self.rmc = GPS.RMC_Frame(
            valid=valid,
            timestamp=timestamp,
            latitude=latitude,
            longitude=longitude,
            knots=knots,
            course=course,
        )

    def get_last_rmc_frame(self):
        if self.rmc.timestamp:
            return self.rmc
        return {}
