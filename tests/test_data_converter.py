# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


import os
from unittest import TestCase
from mat.data_converter import DataConverter
from mat.data_file_factory import create_data_file
from tests.utils import (
    assert_compare_expected_file,
    reference_file
)
from mat.data_file import _sensors_from_names


class TestDataConverter(TestCase):
    def test_creation(self):
        assert DataConverter('no file')

    def test_factory_no_filename(self):
        with self.assertRaises(ValueError):
            create_data_file('')

    # THIS IS THE GOAL
    # def test_conversion(self):
    #     full_file_path = reference_file("test.lid")
    #     converter = DataConverter(full_file_path)
    #     converter.convert()
    #     assert_compare_expected_file("test_accelmag.csv")
    #     assert_compare_expected_file("test_temperature.csv")

    def test_data_file_creation(self):
        full_file_path = reference_file("test.lid")
        converter = DataConverter(full_file_path,
                                  output_type='discrete',
                                  output_format='csv')

    def test_sensors_from_names(self):
        full_file_path = reference_file("test.lid")
        f = create_data_file(full_file_path)
        sensors = f.sensors().sensors()
        accel_mag = _sensors_from_names(sensors,
                                        ['Accelerometer', 'Magnetometer'])
        assert ['Accelerometer', 'Magnetometer'] == [x.name for x in accel_mag]


    def test_verify_outputter_current(self):
        full_file_path = reference_file("test.lid")
        dc = DataConverter(full_file_path, output_type='current')
        outputters = dc._open_outputs()
        pass
