from mat.gps import (
    parse_int,
    parse_float,
    GPS
)
from contextlib import contextmanager
from unittest.mock import patch
from unittest import TestCase


class FakeSerial:
    def __init__(self, fakeport, fakebaudrate):
        pass

    def readline(self):
        return b'$GPRMC,210239.000,A,4134.2946,N,07038.2859,W,0.00,196.76,041218,,,A*77'


class FakeSerialWrongChecksum(FakeSerial):
    def readline(self):
        return b'$GPRMC,210239.000,A,4134.2946,N,07038.2859,W,0.00,196.76,041218,,,A*11'


@contextmanager
def _patch_serial(fake_serial_class):
    with patch('serial.Serial', fake_serial_class):
        yield


class TestGPS(TestCase):
    # check: http://www.hiddenvision.co.uk/ez/?nmea_lat=3015.4550S&nmea_lon=
    def test_convert_lat_n(self):
        lat_str = '3015.4550'
        assert GPS._to_decimal_degrees(lat_str, 'N') == 30.257583333333333

    def test_convert_lat_s(self):
        lat_str = '3015.4550'
        assert GPS._to_decimal_degrees(lat_str, 'S') == -30.257583333333333

    def test_convert_lon_e(self):
        lon_str = '07301.3281'
        assert GPS._to_decimal_degrees(lon_str, 'E') == 73.022135

    def test_convert_lon_w(self):
        lon_str = '07301.3281'
        assert GPS._to_decimal_degrees(lon_str, 'W') == -73.022135

    def test_convert_lon_too_short(self):
        lon_str = '807.2500'
        with self.assertRaises(ValueError):
            GPS._to_decimal_degrees(lon_str, 'W')

    def test_to_decimal_value_none(self):
        assert GPS._to_decimal_degrees('', 'SW') is None

    def test_to_decimal_value_existing(self):
        assert GPS._to_decimal_degrees('4119.6607', 'SW') == -41.32767833333333

    def test_parse_int(self):
        assert parse_int('3') == 3

    def test_parse_float(self):
        assert parse_float('3.5') == 3.5

    def test_gps_read_line(self):
        with _patch_serial(FakeSerial):
            o = GPS('any', 115200)
            frame = o.read_line()
            assert frame is not None

    def test_gps_read_line_wrong_checksum(self):
        with _patch_serial(FakeSerialWrongChecksum):
            o = GPS('any', 115200)
            frame = o.read_line()
            assert frame is None

    def test_my_measures(self):
        with _patch_serial(FakeSerial):
            last_rmc = GPS.RMC_Frame(True, '2018-11-21 18:21:52', 42.0003,
                                     69.9835, 0.56, 190.22)
            o = GPS('any', 115200)
            o.rmc = last_rmc
            expected = GPS.RMC_Frame(True, '2018-11-21 18:21:52', 42.0003,
                                     69.9835, 0.56, 190.22)
            assert o.get_last_rmc_frame() == expected
