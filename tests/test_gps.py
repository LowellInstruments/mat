from mat.gps import (
    to_decimal_degrees,
    parse_int,
    parse_float,
    GPS
)
from contextlib import contextmanager
from mock import patch


class FakeSerial:
    def __init__(self, fakeport, fakebaudrate):
        pass

    def readline(self):
        return b'$GPGGA,150455.000,4138.4356,N,07037.2775,\
        W,2,06,1.6,15.9,M,-34.3,M,3.0,0*1234'


@contextmanager
def _patch_serial():
    with patch("serial.Serial", FakeSerial):
        yield


@contextmanager
def _patch_gps_read_line(rv_read_line):
    with patch("serial.Serial", FakeSerial):
        with patch("mat.gps.GPS.read_line", return_value=rv_read_line):
            yield


class TestGPS:
    # check: http://www.hiddenvision.co.uk/ez/?nmea_lat=3015.4550S&nmea_lon=
    def test_convert_lat_n(self):
        lat_str = "3015.4550"
        assert to_decimal_degrees(lat_str, "N") == 30.257583333333333

    def test_convert_lat_s(self):
        lat_str = "3015.4550"
        assert to_decimal_degrees(lat_str, "S") == -30.257583333333333

    def test_convert_lon_e(self):
        lon_str = "07301.3281"
        assert to_decimal_degrees(lon_str, "E") == 73.022135

    def test_convert_lon_w(self):
        lon_str = "07301.3281"
        assert to_decimal_degrees(lon_str, "W") == -73.022135

    def test_to_decimal_value_none(self):
        assert to_decimal_degrees("", "SW") is None

    def test_to_decimal_value_existing(self):
        assert to_decimal_degrees("4119.6607", "SW") == -41.32767833333333

    def test_parse_int(self):
        assert parse_int("3") == 3

    def test_parse_float(self):
        assert parse_float("3.5") == 3.5

    def test_gps_read_line(self):
        with _patch_serial():
            o = GPS("any", 115200)
            # careful, number of tabs in broken line must match read_line()
            assert o.read_line() == b'$GPGGA,150455.000,4138.4356,N,07037.2775,\
        W,2,06,1.6,15.9,M,-34.3,M,3.0,0*1234'

    def test_gps_parse_line_rmc_ok(self):
        with _patch_gps_read_line(b'$GPRMC,150455.000,A,4138.4356,N,\
        07037.2775,W,0.00,61.63,211118,,,D*1234'):
            o = GPS("any", 115200)
            assert o.parse_line() is True

    def test_gps_parse_line_empty(self):
        with _patch_gps_read_line(b''):
            o = GPS("any", 115200)
            assert o.parse_line() is False

    def test_my_measures(self):
        with _patch_serial():
            rmc_dict = {'valid': True,
                        'timestamp': '2018-11-21 18:21:52',
                        'latitude': 42.0003,
                        'longitude': 69.9835,
                        'knots': 0.56,
                        'course': 190.22
                        }
            o = GPS("any", 115200)
            o.rmc = rmc_dict
            expected = {'rmc_latitude': '42.0003',
                        'rmc_longitude': '69.9835',
                        'rmc_timestamp': '2018-11-21 18:21:52'
                        }
            print(o.get_last_rmc_frame())
            print(expected)
            assert o.get_last_rmc_frame() == expected
