import datetime
from mat.gps import _gps_parse_rmc_frame


class TestGPSQuectel:

    def test_gps_parse_rmc_frame(self):
        s = '$GPRMC,220516,A,5133.82,N,00042.24,W,173.8,231.8,130694,004.2,W*70'
        rv = _gps_parse_rmc_frame(s)
        assert rv == (51.56366666666667, -0.7040000000000001,
                      datetime.datetime(1994, 6, 13, 22, 5, 16))

