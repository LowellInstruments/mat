import serial
import datetime
import time
from collections import namedtuple


# how to test this with coverage:
# python3 -m pytest
#       tests/test_gps.py
#       --cov mat.gps_bu_353_s4
#       --cov-report=html:<output_dir>


def parse_int(x):
    return int(x) if x else None


def parse_float(x):
    return float(x) if x else None


RMC_ID = '$GPRMC'


class GPS:
    """ 
        GPS class for USB device BU_353_S4
        waits for and parses GPS RMC frames
    """

    BAUD_RATE_BU_353_S4 = 4800
    RMC_Frame = namedtuple('RMC_Frame',
                           'valid timestamp '
                           'latitude '
                           'longitude '
                           'knots '
                           'course')

    def __init__(self, port, br=BAUD_RATE_BU_353_S4):
        try:
            self.port = serial.Serial(port, br)
        except serial.SerialException:
            print('GPS: port exception {}'.format(port))
            self.port = None
        self.handlers = {
            RMC_ID: self._on_rmc,
        }
        self.last_rmc = None

    @staticmethod
    def _to_deg(value, nsew):
        # BU-353-S4 lat, lon: DDMM.mmmm, or empty if no coverage
        if not value:
            return None
        a, b = value.split('.')
        if len(a) < 4:
            raise ValueError
        degrees = int(a) // 100
        minutes = int(a) % 100
        minutes += float(int(b) / 10 ** len(b))
        result = degrees + minutes / 60.0
        if nsew in 'SW':
            result = -result
        return result

    def _on_rmc(self, a):
        # populates self.last_rmc on success
        if a[1] != 'A':
            return
        t = datetime.datetime.strptime(a[8] + a[0], '%d%m%y%H%M%S.%f')
        lat = GPS._to_deg(a[2], a[3])
        lon = GPS._to_deg(a[4], a[5])
        knots = parse_float(a[6])
        course = parse_float(a[7])
        self.last_rmc = GPS.RMC_Frame(a[1], t, lat, lon, knots, course)

    @staticmethod
    def _verify_string(data, checksum):
        # lose '$' character at the beginning of gps_bu_353_s4 sentence
        data = data[1:]
        crc_as_dec = int(checksum, 16)
        int_values = [ord(x) for x in data]
        crc = 0
        for x in int_values:
            crc = crc ^ x
        return crc == crc_as_dec

    def _parse_line(self, b: bytes, f_t):
        """
        Parse a GPS string and call its handler, if any
        :param b: bytes from USB
        :param f_t: frame_type expected, e.g. '$GPRMC'
        :return: GPS full string or None
        """
        try:
            if b.startswith('$'.encode('ASCII')):
                s = b.decode('ASCII')
                data, checksum = s.split('*')
                tokens = data.split(',')
                f_t, a = tokens[0], tokens[1:]
                h = self.handlers.get(f_t)
                if GPS._verify_string(data, checksum) is False\
                        or f_t != f_t \
                        or h is None:
                    return None
                # try to populate self.last_rmc
                h(a)
                return s
            return None
        except (ValueError, AttributeError):
            return None

    def _wait_frame(self, f_t, timeout):
        """
        Listens for a GPS frame
        :param f_t: frame_type expected, e.g. '$GPRMC'
        :param timeout: how long till failure
        :return: GPS string if OK else None
        """
        till = time.perf_counter() + timeout
        while 1:
            if time.perf_counter() >= till:
                return None
            b = self.port.readline().strip()
            rx = self._parse_line(b, f_t)
            if rx:
                return rx
            time.sleep(0.1)

    def get_gps_info(self, timeout=3) -> namedtuple:
        if not self.port:
            return None

        if self._wait_frame('$GPRMC', timeout):
            # fields needed to consider RMC frame as valid
            if self.last_rmc and self.last_rmc.timestamp:
                return self.last_rmc
        return None
