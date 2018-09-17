import numpy as np
from math import floor


class SensorFilter:
    def __init__(self, spec, header):
        self.channels = spec.channels
        self.interval = header.tag(spec.interval_tag)
        self.burst_rate = header.tag(spec.burst_rate_tag) or 1
        self.burst_count = header.tag(spec.burst_count_tag) or 1
        self.data_type = spec.data_type
        self.is_sensor = None

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

    def parse_data_page(self, data_page):
        index = self.is_sensor[self.is_sensor < len(data_page)]
        sensor_data = self._remove_partial_burst(data_page[index])
        sensor_data = sensor_data.astype(self.data_type)
        return np.reshape(sensor_data, (self.channels, -1), order='F')

    def _remove_partial_burst(self, sensor_data):
        samples_per_burst = self.burst_count * self.channels
        n_bursts = floor(len(sensor_data) / samples_per_burst)
        return sensor_data[:n_bursts * samples_per_burst]
