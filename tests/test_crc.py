import os
from mat.crc import calculate_local_file_crc


class TestMatCRC:
    def test_mat_crc(self):
        path_local = 'files/bad.lid'
        path_abs = 'tests/files/bad.lid'
        path = path_abs if os.getenv('GITHUB_ACTIONS') else path_local
        assert calculate_local_file_crc(path) == '4a745ad9'
