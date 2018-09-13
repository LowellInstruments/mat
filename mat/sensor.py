from abc import ABC, abstractmethod
from mat.time_sequence import TimeSequence
from mat.sensor_filter import SensorFilter
import mat.converter as converter
from mat.accelerometer_factory import accelerometer_factory
from mat.magnetometer_factory import magnetometer_factory


class AbstractSensorFactory(ABC):
    def __init__(self, header, calibration):
        self.header = header
        self.calibration = calibration

    @abstractmethod
    def make_time_sequence(self):
        pass

    @abstractmethod
    def make_sensor_filter(self):
        pass

    @abstractmethod
    def make_calibration(self):
        pass


class AccelSensorFactory(AbstractSensorFactory):
    def make_time_sequence(self):
        interval = self.header['ORI']
        frequency = self.header['BMR']
        burst_length = self.header['BMN']
        page_seconds = 1000  # 1000 is a placeholder for value TBD
        return TimeSequence(interval, frequency, burst_length, page_seconds)

    def make_sensor_filter(self):
        burst_length = self.header['BMN']
        channels = 3
        data_type = 'int16'
        return SensorFilter(burst_length, channels, data_type)

    def make_calibration(self):
        return accelerometer_factory(self.calibration)


class MagSensorFactory(AccelSensorFactory):
    def make_calibration(self):
        return magnetometer_factory(self.calibration)


class Sensor:
    def __init__(self, header, calibration):


################
self.active_sensors = []
if 'TMP' in self.header and self.header['TMP'] == 1:
    pass

if 'ACL' in self.header and self.header['ACL'] == 1:
    self.active_sensors.append(AccelSensorFactory(header, calibration))

if 'MGN' in self.header and self.header['MGN'] == 1:
    self.active_sensors.append(MagSensorFactory(header, calibration))

