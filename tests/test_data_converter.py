# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


from unittest import TestCase
from mat.data_converter import DataConverter
from mat.data_file_factory import load_data_file
from tests.utils import reference_file
from tests.utils import compare_files


class TestDataConverter(TestCase):
    def test_creation(self):
        assert DataConverter('no file')

    def test_factory_no_filename(self):
        with self.assertRaises(ValueError):
            load_data_file('')

    # THIS IS THE GOAL
    def test_conversion(self):
        full_file_path = reference_file('test.lid')
        converter = DataConverter(full_file_path, average=False)
        converter.convert()
        compare_files(reference_file('test_AccelMag.csv'),
                      reference_file('test_accelmag.csv.expect'))
        compare_files(reference_file('test_Temperature.csv'),
                      reference_file('test_temperature.csv.expect'))

    def test_data_converter_creation(self):
        full_file_path = reference_file("test.lid")
        DataConverter(full_file_path,
                      output_type='discrete',
                      output_format='csv')

    def test_observer(self):
        full_file_path = reference_file('test.lid')
        dc = DataConverter(full_file_path)
        dc.register_observer(lambda x: None)
        dc.convert()

    def test_convert(self):
        full_file_path = reference_file('test.lid')
        dc = DataConverter(full_file_path, time_format='legacy')
        dc.convert()

    # def test_current(self):
    #     full_file_path = reference_file('test.lid')
    #     dc = DataConverter(full_file_path, output_type='current')
    #     dc.convert()
    #
    # def test_compass(self):
    #     full_file_path = reference_file('test.lid')
    #     dc = DataConverter(full_file_path, output_type='compass')
    #     dc.convert()
