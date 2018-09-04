import os
from unittest import TestCase
from mat import header


class TestHeader(TestCase):
    def test_header(self):
        expected_dict = {'SER': '1805225', 'FWV': '1.8.32.5', 'DPL': 2,
                         'DFS': '0x8000', 'STM': '1970-01-01 00:00:00',
                         'ETM': '4096-01-01 00:00:00', 'LED': True,
                         'CLK': '2018-05-25 08:27:07', 'TMP': True,
                         'ACL': True, 'MGN': True, 'TRI': 10, 'ORI': 10,
                         'BMR': 8, 'BMN': 8, 'BAT': '0e5e', 'PWC': '0001',
                         'STS': 1, 'PRS': False, 'PHD': False, 'PRR': 4,
                         'PRN': 4}
        h = header.parse_header(reference_file('test.lid'))
        assert h == expected_dict

    def test_bad_header(self):
        with self.assertRaises(ValueError):
            h = header.parse_header(reference_file('bad_header.lid'))

    def test_missing_hds(self):
        with self.assertRaises(ValueError):
            h = header.parse_header(reference_file('missing_hds_header.lid'))



def reference_file(file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "files",
        file_name)
