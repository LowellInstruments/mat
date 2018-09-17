from mat.sensor_specification import AVAILABLE_SENSORS
import numpy as np


class SensorGroup:
    def __init__(self, header, calibration):
        self.header = header
        self._active_sensors = None
        self.data_page = None
        self.calibration = calibration

    def sensors(self):
        if self._active_sensors:
            return self._active_sensors
        self._active_sensors = self._equip()
        return self._active_sensors

    def samples_per_time(self, seconds):
        return len(self.time_and_order(seconds))

    def _equip(self):
        active_sensors = []
        for spec in AVAILABLE_SENSORS:
            if self.header.tag(spec.enabled_tag):
                active_sensors.append(Sensor(spec,
                                             self.header,
                                             self.calibration))
        return active_sensors

    def load_sequence_into_sensors(self, seconds):
        time_and_order = self.time_and_order(seconds)
        for sensor in self.sensors():
            is_sensor = [s[1] == sensor.order for s in time_and_order]
            sensor.is_sensor = np.array(is_sensor)

    def sensor_names(self):
        return [sensor.name for sensor in self.sensors()]

    def time_and_order(self, seconds):
        """
        Return a full time and sensor order sequence for all active sensors.
        The output is a list of tuples containing the sample time and order
        sorted by time, then by order.
        """
        time_and_order = []
        for sensor in self.sensors():
            sample_times = sensor.time_sequence(seconds)
            sensor_time_order = [(t, sensor.order) for t in sample_times]
            time_and_order.extend(sensor_time_order)
        return sorted(time_and_order)


class Sensor:
    def __init__(self, spec, header, calibration):
        self.name = spec.name
        self.order = spec.order
        self.channels = spec.channels
        self.interval = header.tag(spec.interval_tag)
        self.burst_rate = header.tag(spec.burst_rate_tag) or 1
        self.burst_count = header.tag(spec.burst_count_tag) or 1
        self.is_sensor = None
        self.converter = spec.converter(calibration)

    def time_sequence(self, seconds):
        """
        Returns a list of all sample times that occur between 0 and 'seconds'
        """
        sample_times = []
        for interval_time in range(0, seconds, self.interval):
            for burst_time in range(0, self.burst_count):
                burst = [interval_time + burst_time / self.burst_rate]
                burst *= self.channels
                sample_times.extend(burst)
        return sample_times

    def apply_calibration(self, data):
        return self.converter.convert(data)

    def parse_sensor(self, data_page):
        return data_page[self.is_sensor]
