from mat.crc import calculate_local_file_crc


class TestMatCRC:
    def test_mat_crc(self):
        assert calculate_local_file_crc('files/bad.lid') == '4a745ad9'
