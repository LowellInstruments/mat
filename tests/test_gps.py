from mat.gps import (
    convert_lat,
    convert_lon,
    convert_time,
    verify_string
)


class TestGPS:
    # 4119.6607,N,07301.3281,W
    def test_convert_lat_n(self):
        lat_str = "4119.6607"
        assert convert_lat(lat_str, "N") == 41 + 19.6607/60

    def test_convert_lat_s(self):
        lat_str = "4119.6607"
        assert convert_lat(lat_str, "S") == -41 - 19.6607/60

    def test_convert_lon_e(self):
        lat_str = "07301.3281"
        assert convert_lon(lat_str, "E") == 73 + 1.3281/60

    def test_convert_lon_w(self):
        lat_str = "17301.3281"
        assert convert_lon(lat_str, "W") == -173 - 1.3281/60

    def test_verify(self):
        string = ('$GPGGA,125742.000,4119.6607,N,07301.3281,'
                  'W,1,09,1.0,100.3,M,-34.3,M,,0000*6D')
        assert verify_string(string) == True

    def test_bad_string(self):
        string = ('125742.000,4119.6607,N,07301.3281,'
                  'W,1,09,1.0,100.3,M,-34.3,M,,0000*6D')
        assert verify_string(string) == False

    def correct_format_bad_checksum(self):
        string = ('$GPGGA,225742.000,4119.6607,N,07301.3281,'
                  'W,1,09,1.0,100.3,M,-34.3,M,,0000*6D')
        assert verify_string(string) == False

    def test_convert_time(self):
        time_str = convert_time('125742.000')
        assert time_str == '12:57:42'
