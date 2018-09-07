import numpy as np
from math import floor


class SensorFilter:
    def __init__(self, burst_length=1, channels=1, data_type='int16'):
        self.index = np.array([])
        self.burst_length = burst_length
        self.channels = channels
        self.data_type = data_type

    def add_to_index(self, position):
        self.index = np.append(self.index, position)

    def parse_data_page(self, data_page):
        index = self.index[self.index < len(data_page)]
        sensor_data = self._remove_partial_burst(data_page[index])
        return np.reshape(sensor_data, (self.channels, -1), order='F')

    def _remove_partial_burst(self, sensor_data):
        samples_per_burst = self.burst_length * self.channels
        n_bursts = floor(len(sensor_data) / samples_per_burst)
        return sensor_data[:n_bursts * samples_per_burst]
