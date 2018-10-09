from mat.sensor_specification import AVAILABLE_SENSORS
import numpy as np
from math import floor


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
        time_and_order.extend(sensor_time_order)
    return sorted(time_and_order)


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


class Sensor:
    def __init__(self, sensor_spec, header, calibration, seconds):
        self.sensor_spec = sensor_spec
        self.name = sensor_spec.name
        self.channels = sensor_spec.channels
        self.interval = header.tag(sensor_spec.interval_tag)
        self.burst_rate = header.tag(sensor_spec.burst_rate_tag) or 1
        self.burst_count = header.tag(sensor_spec.burst_count_tag) or 1
        self.data_type = sensor_spec.data_type
        self.is_sample = None
        self.seconds = seconds
        self.order = sensor_spec.order
        self.converter = sensor_spec.converter(calibration)
        self.cache = {'page_time': None, 'data': None}

    def full_sample_times(self):
        """
        The elapsed time in seconds from the start of the data page when a
        sensor samples. n channel sensors return n times per sample.
        """
        sample_times = []
        for interval_time in range(0, self.seconds, self.interval):
            for burst_time in range(0, self.burst_count):
                burst_time = [interval_time + burst_time / self.burst_rate]
                sample_times.extend([burst_time] * self.channels)
        return np.array(sample_times)

    def _parse_page(self, data_page):
        """
        Return raw data and time as a tuple
        """
        index = self.is_sample[:len(data_page)]
        sensor_data = self._remove_partial_burst(data_page[index])
        sensor_data = self._reshape_to_n_channels(sensor_data)
        sensor_data = sensor_data.astype(self.data_type)
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
        data = np.mean(np.reshape(data, (3, -1, self.burst_count)), axis=2)
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
        temp, temp_time = self.temperature.convert(data_page,
                                                   average,
                                                   page_time)
        temp_interp = np.interp(time, temp_time, temp[0, :])
        data = self.converter.convert(raw_data, temp_interp)
        if average:
            data, time = self._average_bursts(data, time)
        time += page_time
        return data, time
