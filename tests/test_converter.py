from unittest import TestCase
from numpy import array
from mat.converter import Converter
from mat.v3_calibration import V3Calibration
from mat.light import DEFAULT_PDA
from mat.pressure import DEFAULT_PRA
from utils import (
    calibration_from_file,
)


ZERO_ARRAY = array([0])
TEMP_ARRAY = array([1])
CUBIC_IDENTITY = array([[1, 0, 0],
                        [0, 1, 0],
                        [0, 0, 1]])
CUBIC_TEMP_ARRAY = array([1, 1, 1])


class TestConverter(TestCase):
    def test_empty_calibration(self):
        with self.assertRaises(KeyError):
            Converter(V3Calibration({}))

    def test_calibrated_temperature(self):
        assert Converter(
            calibration_from_file("v3_calibration.txt")).temperature(
                TEMP_ARRAY).shape == (1, )

    def test_calibrated_pressure(self):
        assert Converter(
            calibration_from_file("v3_calibration.txt")).pressure(
            ZERO_ARRAY) == array([DEFAULT_PRA])

    def test_calibrated_light(self):
        assert Converter(
            calibration_from_file("v3_calibration.txt")).light(
            ZERO_ARRAY) == array([DEFAULT_PDA])

    def test_missing_accelerometer(self):
        assert Converter(
            calibration_from_file("v3_missing_tags.txt")).accelerometer(
            CUBIC_IDENTITY) is None

    def test_calibrated_linear_accelerometer(self):
        assert Converter(
            calibration_from_file("v2_linear_acc.txt")).accelerometer(
            CUBIC_IDENTITY).shape == (3, 3)

    def test_calibrated_cubic_accelerometer(self):
        assert Converter(
            calibration_from_file("v3_calibration.txt")).accelerometer(
            CUBIC_IDENTITY).shape == (3, 3)

    def test_missing_magnetometer(self):
        assert Converter(
            calibration_from_file("v3_missing_tags.txt")).magnetometer(
            CUBIC_IDENTITY) is None

    def test_calibrated_cubic_magnetometer(self):
        assert Converter(
            calibration_from_file("v3_calibration.txt")).magnetometer(
            CUBIC_IDENTITY).shape == (3, 3)

    def test_calibrated_temp_comp_magnetometer_with_no_temp(self):
        assert Converter(
            calibration_from_file("v3_temp_comp.txt")).magnetometer(
                CUBIC_IDENTITY).shape == (3, 3)

    def test_calibrated_temp_comp_magnetometer(self):
        assert Converter(
            calibration_from_file("v3_temp_comp.txt")).magnetometer(
                CUBIC_IDENTITY, CUBIC_TEMP_ARRAY).shape == (3, 3)
