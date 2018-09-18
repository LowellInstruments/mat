from mat.sensor_specification import AVAILABLE_SENSORS
import numpy as np
from mat.sensor_filter import SensorFilter


class SensorFactory:
    def __init__(self, header, calibration, seconds):
        self.header = header
        self.calibration = calibration
        self.seconds = seconds
        self.sensors_list = None

    def get_sensors(self):
        self._build_sensors()
        # with sensors discovered, determine the overall sensor sequence
        # and let the individual sensors know their positions
        time_and_order = self._time_and_order(self.sensors_list,
                                              self.seconds)
        self._load_sequence_into_sensors(time_and_order)
        return self.sensors_list

    def _build_sensors(self):
        self.sensors_list = []
        for spec in AVAILABLE_SENSORS:
            if self.header.tag(spec.enabled_tag):
                self.sensors_list.append(Sensor(spec,
                                                self.header,
                                                self.calibration,
                                                self.seconds))

    def _load_sequence_into_sensors(self, time_and_order):
        for sensor in self.sensors_list:
            is_sensor = [s[1] == sensor.order for s in time_and_order]
            sensor.set_filter_sequence(np.array(is_sensor))

    def _time_and_order(self, sensors, seconds):
        """
        Return a full time and sensor order sequence for all active sensors.
        The output is a list of tuples containing the sample time and order
        sorted by time, then by order.
        """
        time_and_order = []
        for sensor in sensors:
            sample_times = sensor.sample_times()
            sensor_time_order = [(t, sensor.order) for t in sample_times]
            time_and_order.extend(sensor_time_order)
        return sorted(time_and_order)


class Sensor:
    def __init__(self, spec, header, calibration, seconds):
        self.spec = spec
        self.name = spec.name
        self.order = spec.order
        self.sensor_filter = SensorFilter(spec, header, seconds)
        self.converter = spec.converter(calibration)

    def sample_times(self):
        return self.sensor_filter.sample_times()

    def set_filter_sequence(self, is_sensor):
        self.sensor_filter.is_sensor = is_sensor

    def apply_calibration(self, data):
        return self.converter.convert(data)

    def parse(self, data_page):
        return self.sensor_filter.parse_data_page(data_page)

    def samples_per_page(self):
        return np.sum(self.sensor_filter.is_sensor)
