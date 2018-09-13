# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


import os
from unittest import TestCase
from mat.data_converter import DataConverter
from mat import data_file_factory
from tests.utils import (
    assert_compare_expected_file,
    reference_file
)


class TestDataConverter(TestCase):
    def test_creation(self):
        assert DataConverter('no file')

    def test_factory_no_filename(self):
        with self.assertRaises(ValueError):
            data_file_factory.create('')

    # def test_conversion(self):
    #     full_file_path = reference_file("test.lid")
    #     converter = DataConverter(full_file_path, average=False)
    #     converter.convert()
    #     assert_compare_expected_file("test_accelmag.csv")
    #     assert_compare_expected_file("test_temperature.csv")
