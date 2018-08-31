from mat.gps import (
    convert_lat,
    convert_lon,
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
