# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved

import os
from mat.data_converter import DataConverter
from mat.tests.utils import assert_compare_expected_file


class TestDataConverter(object):
    def test_creation(self):
        assert DataConverter("no file")

    def test_conversion(self):
        full_file_path = reference_file("test.lid")
        converter = DataConverter(full_file_path, average=False)
        converter.convert()
        assert_compare_expected_file("test_accelmag.csv")
        assert_compare_expected_file("test_temperature.csv")
