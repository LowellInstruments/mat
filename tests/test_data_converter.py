# GPLv3 License
# Copyright (c) 2018 Lowell Instruments, LLC, some rights reserved


from unittest import TestCase
from mat.data_converter import DataConverter
from mat.data_file_factory import load_data_file
from tests.utils import reference_file
from tests.utils import compare_files
from mat.tiltcurve import TiltCurve
import os
import re


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

    def test_current(self):
        full_file_path = reference_file('test.lid')
        tilt_file_path = reference_file('tiltcurve/TCM-1, No Ballast Washer, '
                                        'Salt Water.cal')
        tilt_curve = TiltCurve(tilt_file_path)
        dc = DataConverter(full_file_path,
                           output_type='current',
                           tilt_curve=tilt_curve)
        dc.convert()

    def test_compass(self):
        full_file_path = reference_file('test.lid')
        dc = DataConverter(full_file_path, output_type='compass')
        dc.convert()

    def test_temp_comp_magnetometer(self):
        path = reference_file('TCM1_Calibrate_(0).lid')
        dc = DataConverter(path)
        dc.convert()

    def test_convert_w_posix_time(self):
        full_file_path = reference_file('test.lid')
        dc = DataConverter(full_file_path, time_format='posix')
        dc.convert()

    def test_two_page_file(self):
        full_file_path = reference_file('two_page_file.lid')
        dc = DataConverter(full_file_path)
        dc.convert()

    def test_current_no_accel(self):
        full_file_path = reference_file('temp_mag_no_accel.lid')
        dc = DataConverter(full_file_path, output_type='current')
        with self.assertRaises(ValueError):
            dc.convert()

    def tearDown(self):
        directory = os.path.dirname(os.path.realpath(__file__))
        directory = os.path.join(directory, 'files')
        for f in os.listdir(directory):
            if re.search(r'.*\.csv$', f):
                os.remove(os.path.join(directory, f))
