from mat.gps import PORT_DATA, PORT_CTRL


class TestGPS:

    def test_gps_mat(self):
        assert PORT_DATA
        assert PORT_CTRL
