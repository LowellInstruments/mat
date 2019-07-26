from mat.sensor_specification import AVAILABLE_SENSORS
import numpy as np
from math import floor
from heapq import merge
from itertools import chain
from mat.header import (
    Header,
    ORIENTATION_INTERVAL,
    TEMPERATURE_INTERVAL,
    IS_ACCELEROMETER,
    IS_MAGNETOMETER,
    IS_TEMPERATURE
)
from mat.type_converter import type_factory


def create_sensors(header, calibration, seconds):
    """
    The sensor filters (sensors) need to be built together because the
    individual sensor sequences depend on the order of all the sensors.
    """
    sensors = _build_sensors(header, calibration, seconds)
    time_and_order = _time_and_order(sensors)
    _load_sequence_into_sensors(sensors, time_and_order)
    _add_temperature_dependency(sensors)
    return sensors


def _build_sensors(header, calibration, seconds):
    sensors = []
    for sensor_spec in AVAILABLE_SENSORS:
        if header.tag(sensor_spec.enabled_tag):
            sensors.append(_sensor_factory(sensor_spec,
                                           header,
                                           calibration,
                                           seconds))
    return sensors


def _sensor_factory(sensor_spec, header, calibration, seconds):
    if sensor_spec.temp_dependant:
        return TempDependantSensor(sensor_spec, header, calibration, seconds)
    return Sensor(sensor_spec, header, calibration, seconds)


def _time_and_order(sensors):
    """
    Return a fully combined time and sensor-order sequence for 'sensors'.
    The output is a list of tuples containing the sample time and order
    sorted by time, then by order.
    """
    time_and_order = []
    for sensor in sensors:
        sample_times = sensor.full_sample_times()
        sensor_time_order = [(t, sensor.order) for t in sample_times]
        time_and_order.append(sensor_time_order)
    return list(merge(*time_and_order))


def _load_sequence_into_sensors(sensors, time_and_order):
    for sensor in sensors:
        is_sample = [s[1] == sensor.order for s in time_and_order]
        sensor.is_sample = np.array(is_sample)


def _add_temperature_dependency(sensors):
    sensor_names = [x.name for x in sensors]
    if 'Temperature' not in sensor_names:
        return
    temp_index = sensor_names.index('Temperature')
    for sensor in sensors:
        if sensor.sensor_spec.temp_dependant:
            sensor.temperature = sensors[temp_index]


def major_interval_bytes(header_dict):
    """
    This is a helper function that will determine the number of bytes in
    a major interval.
    """
    header = Header({})
    header._header = header_dict

    orient_interval = 0
    temperature_interval = 0
    if header.tag(IS_ACCELEROMETER) or header.tag(IS_MAGNETOMETER):
        orient_interval = header.tag(ORIENTATION_INTERVAL)
    if header.tag(IS_TEMPERATURE):
        temperature_interval = header.tag(TEMPERATURE_INTERVAL)
    major_interval = max(orient_interval, temperature_interval)

    sensors = create_sensors(header, None, major_interval)
    bytes = 0
    for s in sensors:
        bytes += s.samples_per_page() * 2
    return bytes


class Sensor:
    def __init__(self, sensor_spec, header, calibration, seconds):
        self.sensor_spec = sensor_spec
        self.name = sensor_spec.name
        self.channels = sensor_spec.channels
        self.interval = header.tag(sensor_spec.interval_tag)
        self.burst_rate = header.tag(sensor_spec.burst_rate_tag) or 1
        self.burst_count = header.tag(sensor_spec.burst_count_tag) or 1
        self.data_type = type_factory(sensor_spec.data_type)
        self.is_sample = None
        self.seconds = seconds
        self.order = sensor_spec.order
        self.cache = {'page_time': None, 'data': None}
        self._full_sample_times_cache = None
        if calibration:
            self.converter = sensor_spec.converter(calibration)

    def full_sample_times(self):
        """
        The elapsed time in seconds from the start of the data page when a
        sensor samples. n channel sensors return n times per sample.
        """
        if self._full_sample_times_cache is None:
            times = [[interval+burst/self.burst_rate]*self.channels
                     for interval in range(0, self.seconds, self.interval)
                     for burst in range(self.burst_count)]
            self._full_sample_times_cache = list(chain.from_iterable(times))
        return self._full_sample_times_cache

    def _parse_page(self, data_page):
        """
        Return raw data and time as a tuple
        """
        index = self.is_sample[:len(data_page)]
        sensor_data = self._remove_partial_burst(data_page[index])
        sensor_data = self._reshape_to_n_channels(sensor_data)
        sensor_data = self.data_type.convert(sensor_data)
        n_samples = sensor_data.shape[1]
        time = self._sample_times()[:n_samples]
        return sensor_data, time

    def _remove_partial_burst(self, sensor_data):
        samples_per_burst = self.burst_count * self.channels
        n_bursts = floor(len(sensor_data) / samples_per_burst)
        return sensor_data[:n_bursts * samples_per_burst]

    def _sample_times(self):
        """
        1-d sample times. If a sensor has n channels, only one time is returned
        for each sample
        """
        full_sample_times = self.full_sample_times()
        full_sample_times = self._reshape_to_n_channels(full_sample_times)
        return full_sample_times[0, :]

    def _average_bursts(self, data, time):
        if self.burst_count == 1:
            return data, time
        data = np.mean(np.reshape(data, (self.channels,
                                         -1,
                                         self.burst_count)), axis=2)
        time = time[::self.burst_count]
        return data, time

    def _reshape_to_n_channels(self, data):
        return np.reshape(data, (self.channels, -1), order='F')

    def samples_per_page(self):
        return np.sum(self.is_sample)

    def convert(self, data_page, average, page_time):
        if self.cache['page_time'] == page_time:
            return self.cache['data']
        raw_data, time = self._parse_page(data_page)
        data = self.converter.convert(raw_data)
        if average:
            data, time = self._average_bursts(data, time)
        time += page_time
        self.cache = {'page_time': page_time, 'data': (data, time)}
        return self.cache['data']


class TempDependantSensor(Sensor):
    def __init__(self, sensor_spec, header, calibration, seconds):
        super().__init__(sensor_spec, header, calibration, seconds)
        self.temperature = None

    def convert(self, data_page, average, page_time):
        if not self.temperature:
            return super().convert(data_page, average, page_time)
        raw_data, time = self._parse_page(data_page)
        time += page_time
        temp, temp_time = self.temperature.convert(data_page,
                                                   average,
                                                   page_time)
        temp_interp = np.interp(time, temp_time, temp[0, :])
        data = self.converter.convert(raw_data, temp_interp)
        if average:
            data, time = self._average_bursts(data, time)
        return data, time
