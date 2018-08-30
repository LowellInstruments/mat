import os
from unittest import TestCase
from mat.lid_data_file import LidDataFile
from mat.lis_data_file import LisDataFile
from mat.sensor_data_file import SensorDataFile


LidDataFile.register()
LisDataFile.register()


class TestSensorDataFile(TestCase):
    def test_create_lid(self):
        data_file = SensorDataFile.create(reference_file("test.lid"))
        assert isinstance(data_file, LidDataFile)

    def test_create_lis(self):
        data_file = SensorDataFile.create(reference_file("test.lis"))
        assert isinstance(data_file, LisDataFile)

    def test_create_bad_file(self):
        with self.assertRaises(ValueError):
            SensorDataFile.create(reference_file("test.xyz"))

    def test_n_pages_lid(self):
        data_file = SensorDataFile.create(reference_file("test.lid"))
        assert data_file.n_pages() == 1

    def test_n_pages_lis(self):
        data_file = SensorDataFile.create(reference_file("test.lis"))
        assert data_file.n_pages() == 1

    def test_n_pages_with_bad_file(self):
        data_file = SensorDataFile.create(reference_file("bad.lid"))
        with self.assertRaises(ValueError):
            data_file.n_pages()

    def test_validate(self):
        data_file = SensorDataFile.create(reference_file("test.lid"))
        assert data_file.validate() is None  # No exception raised

    def test_sensors(self):
        data_file = SensorDataFile.create(reference_file("test.lid"))
        assert data_file.sensors() == []

    def test_load_page(self):
        data_file = SensorDataFile.create(reference_file("test.lid"))
        assert data_file.load_page(1) == ""


def reference_file(file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "files",
        file_name)
