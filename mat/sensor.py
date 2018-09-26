from mat.sensor_specification import AVAILABLE_SENSORS
import numpy as np
from math import floor
from hashlib import md5


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
            if sensor_spec.temp_dependant:
                sensor = TempDependantSensor(sensor_spec,
                                             header,
                                             calibration,
                                             seconds)
            else:
                sensor = Sensor(sensor_spec, header, calibration, seconds)
            sensors.append(sensor)
    return sensors


def _time_and_order(sensors):
    """
    Return a full combines time and sensor-order sequence for 'sensors'.
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
        is_sensor = [s[1] == sensor.order for s in time_and_order]
        sensor.is_sensor = np.array(is_sensor)


def _add_temperature_dependency(sensors):
    sensor_names = [x.name for x in sensors]
    try:
        temp_ind = sensor_names.index('Temperature')
    except ValueError:
        return
    for sensor in sensors:
        if sensor.sensor_spec.temp_dependant:
            sensor.temperature = sensors[temp_ind]


class Sensor:
    def __init__(self, sensor_spec, header, calibration, seconds):
        self.sensor_spec = sensor_spec
        self.name = sensor_spec.name
        self.channels = sensor_spec.channels
        self.interval = header.tag(sensor_spec.interval_tag)
        self.burst_rate = header.tag(sensor_spec.burst_rate_tag) or 1
        self.burst_count = header.tag(sensor_spec.burst_count_tag) or 1
        self.data_type = sensor_spec.data_type
        self.is_sensor = None
        self.seconds = seconds
        self.order = sensor_spec.order
        self.converter = sensor_spec.converter(calibration)
        self.cache = {'md5_hash': None, 'data': None}

    def full_sample_times(self):
        """
        The elapsed time in seconds from the start of the data page when a
        sensor samples. n channel sensors return n times per sample.
        """
        sample_times = []
        for interval_time in range(0, self.seconds, self.interval):
            for burst_time in range(0, self.burst_count):
                burst = [interval_time + burst_time / self.burst_rate]
                burst *= self.channels
                sample_times.extend(burst)
        return np.array(sample_times)

    def sample_times(self):
        """
        1-d sample times. If a sensor has n channels, only one time is returned
        for each sample
        """
        sample_times = self.full_sample_times()
        sample_times = self.reshape_to_n_channels(sample_times)
        return sample_times[0, :]

    def parse_page(self, data_page, average):
        """
        Return raw data and time as a tuple
        """
        index = self.is_sensor[:len(data_page)]
        sensor_data = self._remove_partial_burst(data_page[index])
        sensor_data = self.reshape_to_n_channels(sensor_data)
        sensor_data = sensor_data.astype(self.data_type)
        n_samples = sensor_data.shape[1]
        time = self.sample_times()[:n_samples]
        if average:
            sensor_data, time = self._average_bursts(sensor_data, time)
        return sensor_data, time

    def _remove_partial_burst(self, sensor_data):
        samples_per_burst = self.burst_count * self.channels
        n_bursts = floor(len(sensor_data) / samples_per_burst)
        return sensor_data[:n_bursts * samples_per_burst]

    def _average_bursts(self, data, time):
        if self.burst_count == 1:
            return data, time
        data = np.mean(np.reshape(data, (3, -1, self.burst_count)), axis=2)
        time = time[::self.burst_count]
        return data, time

    def reshape_to_n_channels(self, data):
        return np.reshape(data, (self.channels, -1), order='F')

    def samples_per_page(self):
        return np.sum(self.is_sensor)

    def convert(self, data_page, average, page_time):
        md5_hash = md5(data_page).hexdigest()
        if self.cache['md5_hash'] == md5_hash:
            return self.cache['data']
        raw_data, time = self.parse_page(data_page, average)
        data = self.converter.convert(raw_data)
        time += page_time
        self.cache = {'md5_hash': md5_hash, 'data': (data, time)}
        return self.cache['data']


class TempDependantSensor(Sensor):
    def __init__(self, sensor_spec, header, calibration, seconds):
        super().__init__(sensor_spec, header, calibration, seconds)
        self.temperature = None

    def convert(self, data_page, average, page_time):
        if not self.temperature:
            return super().convert(data_page, average, page_time)
        temp, temp_time = self.temperature.convert(data_page,
                                                   average,
                                                   page_time)
        raw_data, time = self.parse_page(data_page, average)
        time += page_time
        temp_interp = np.interp(time, temp_time, temp[0, :])
        data = self.converter.convert(raw_data, temp_interp)
        return data, time
