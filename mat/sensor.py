from collections import namedtuple


SensorSpec = namedtuple('SensorSpec', [
    'name',
    'tag',
    'priority',
    'channels',
    'interval_tag',
    'burst_rate_tag',
    'burst_count_tag',
    'data_type']
)

AVAILABLE_SENSORS = [
    SensorSpec('Temperature', 'TMP', 1, 1, 'TRI', None, None, 'uint16'),
    SensorSpec('Pressure', 'PRS', 2, 1, 'ORI', 'PRR', 'PRN', 'uint16'),
    SensorSpec('Light', 'PHD', 3, 1, 'TRI', None, None, 'uint16'),
    SensorSpec('Accelerometer', 'ACL', 4, 3, 'ORI', 'BMR', 'BMN', 'int16'),
    SensorSpec('Magnetometer', 'MGN', 5, 3, 'ORI', 'BMR', 'BMN', 'int16')
]


class SensorGroup:
    def __init__(self, header):
        self.header = header
        self.active_sensors = []

    def equip(self):
        for spec in AVAILABLE_SENSORS:
            if self.header.tag(spec.tag):
                self.active_sensors.append(Sensor(spec, self.header))
        self._verify_priority()

    def data_sequence(self, page_seconds):
        time_priority = []
        for sensor in self.active_sensors:
            time_offset = sensor.time_offset(page_seconds)
            sensor_time_priority = [(t, sensor.priority) for t in time_offset]
            time_priority.extend(sensor_time_priority)
        return sorted(time_priority)

    def _verify_priority(self):
        priority = [spec.priority for spec in self.active_sensors]
        if len(priority) != len(set(priority)):
            raise ValueError('There cannot be more than one sensor with '
                             'the same priority')


class Sensor:
    def __init__(self, spec, header):
        self.name = spec.name
        self.priority = spec.priority
        self.channels = spec.channels
        self.interval = header.tag(spec.interval_tag)
        self.burst_rate = header.tag(spec.burst_rate_tag) or 1
        self.burst_count = header.tag(spec.burst_count_tag) or 1
        self.data_type = spec.data_type

    def time_offset(self, seconds):
        time_offset = []
        for interval_time in range(0, seconds, self.interval):
            for burst_time in range(0, self.burst_count):
                time_offset.append(interval_time + burst_time / self.burst_rate)
        return time_offset
