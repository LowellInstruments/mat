from mat.output_stream import output_stream_factory
from abc import ABC, abstractmethod
from mat.utils import roll_pitch_yaw, apply_declination
from collections import namedtuple
from numpy import (
    arccos,
    arctan2,
    array,
    cos,
    deg2rad,
    degrees,
    dot,
    mod,
    pi,
    reshape,
    sin,
    sqrt,
    vstack
)


SensorDataTime = namedtuple('SensorDataTime', ['data', 'time'])


def data_product_factory(file_path, sensors, parameters):
    """
    Instantiate a data product subclass and pass it the necessary sensors
    """
    special_cases = {'compass': Compass,
                     'current': Current,
                     'ypr': YawPitchRoll}
    data_products = []
    output_stream = output_stream_factory(file_path, parameters)

    # special cases and accelmag are mutually exclusive, hence the if elif
    if parameters['output_type'] in special_cases.keys():
        klass = special_cases[parameters['output_type']]
        data_products.append(klass(sensors, parameters, output_stream))

    # no special cases, but were accel and mag enabled? If so bundle them
    elif set(AccelMag.REQUIRED_SENSORS).issubset([s.name for s in sensors]):
        data_products.append(AccelMag(sensors, parameters, output_stream))

    # Convert remaining sensors as discrete channels
    remaining_sensors = _remaining_sensors(sensors, data_products)
    for sensor in remaining_sensors:
        data_products.append(DiscreteChannel(sensor,
                                             parameters,
                                             output_stream))
    return data_products


def _remaining_sensors(sensors, data_products):
    used_sensors = [s for p in data_products for s in p.REQUIRED_SENSORS]
    return [s for s in sensors if s.name not in used_sensors]


class DataProduct(ABC):
    OUTPUT_TYPE = ''
    REQUIRED_SENSORS = []

    def __init__(self, sensors, parameters, output_stream):
        self.sensors = self._get_required_sensors(sensors)
        self.parameters = parameters
        self.output_stream = output_stream
        self.average = parameters['average']
        self.split = parameters['split']
        self.configure_output_stream()

    def _get_required_sensors(self, sensors):
        sensor_names = [s.name for s in sensors]
        if not set(self.REQUIRED_SENSORS).issubset(sensor_names):
            raise ValueError('Not all required sensors present')
        return [s for s in sensors if s.name in self.REQUIRED_SENSORS]

    def configure_output_stream(self):
        name = self.stream_name()
        self.output_stream.add_stream(name)
        self.output_stream.set_data_format(name, self.data_format())
        self.output_stream.set_column_header(name, self.column_header())

    def convert_sensors(self, data_page, page_time):
        converted = []
        for sensor in self.sensors:
            data, time = sensor.convert(data_page, self.average, page_time)
            converted.append(SensorDataTime(data, time))
        return converted

    @abstractmethod
    def stream_name(self):
        pass  # pragma: no cover

    @abstractmethod
    def data_format(self):
        pass  # pragma: no cover

    @abstractmethod
    def column_header(self):
        pass  # pragma: no cover

    @abstractmethod
    def process_page(self, data_page, page_time):
        pass  # pragma: no cover


class DiscreteChannel(DataProduct):
    OUTPUT_TYPE = 'discrete'
    REQUIRED_SENSORS = []

    def __init__(self, sensor, parameters, output_stream):
        super().__init__([sensor], parameters, output_stream)

    def _get_required_sensors(self, sensors):
        return sensors

    def stream_name(self):
        return self.sensors[0].name

    def data_format(self):
        return self.sensors[0].sensor_spec.format

    def column_header(self):
        return self.sensors[0].sensor_spec.header

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        self.output_stream.write(self.sensors[0].name,
                                 converted[0].data,
                                 converted[0].time)


class AccelMag(DataProduct):
    OUTPUT_TYPE = 'accelmag'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def stream_name(self):
        return 'AccelMag'

    def data_format(self):
        return self._join_spec_fields('format')

    def column_header(self):
        return self._join_spec_fields('header')

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        data = vstack((converted[0].data, converted[1].data))
        self.output_stream.write(self.stream_name(), data, converted[0].time)

    def _join_spec_fields(self, field):
        fields = [getattr(x.sensor_spec, field) for x in self.sensors]
        return ','.join(fields)


class Current(DataProduct):
    OUTPUT_TYPE = 'current'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def __init__(self, sensors, parameters, output_stream):
        super().__init__(sensors, parameters, output_stream)
        self.tilt_curve = self.parameters['tilt_curve']
        self.declination = self.parameters['declination']

    def stream_name(self):
        return 'Current'

    def data_format(self):
        return '{:0.2f},{:0.2f},{:0.2f},{:0.2f}'

    def column_header(self):
        return ('Speed (cm/s),'
                'Heading (degrees),'
                'Velocity-N (cm/s),'
                'Velocity-E (cm/s)')

    def _calc_tilt_and_heading(self, accel, mag):
        roll, pitch, yaw = roll_pitch_yaw(accel, mag)
        x = -cos(roll) * sin(pitch)
        y = sin(roll)

        tilt = arccos(
            accel[2] / sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2))
        is_usd = tilt > pi / 2
        tilt[is_usd] = pi - tilt[is_usd]

        heading = arctan2(y, x) + yaw
        heading = mod(heading + deg2rad(self.declination), 2 * pi)
        return tilt, heading

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        accel = converted[0].data
        mag = converted[1].data
        tilt, heading = self._calc_tilt_and_heading(accel, mag)
        speed = self.tilt_curve.speed_from_tilt(degrees(tilt))

        velocity_n = speed * cos(heading)
        velocity_e = speed * sin(heading)

        data = vstack((speed, degrees(heading), velocity_n, velocity_e))

        self.output_stream.write(self.stream_name(), data, converted[0].time)


class Compass(DataProduct):
    OUTPUT_TYPE = 'compass'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def __init__(self, sensors, parameters, output_stream):
        super().__init__(sensors, parameters, output_stream)
        self.declination = self.parameters['declination']

    def stream_name(self):
        return 'Heading'

    def data_format(self):
        return '{:0.2f}'

    def column_header(self):
        return 'Heading (degrees)'

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        accel = converted[0].data
        mag = converted[1].data
        m = array([[0, 0, 1], [0, -1, 0], [1, 0, 0]])
        accel = dot(m, accel)
        mag = dot(m, mag)
        roll, pitch, heading = roll_pitch_yaw(accel, mag)
        heading = apply_declination(degrees(heading), self.declination)
        heading = reshape(heading, (1, -1))
        self.output_stream.write(self.stream_name(),
                                 heading,
                                 converted[0].time)


class YawPitchRoll(DataProduct):
    OUTPUT_TYPE = 'ypr'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def __init__(self, sensors, parameters, output_stream):
        super().__init__(sensors, parameters, output_stream)
        self.declination = self.parameters['declination']

    def stream_name(self):
        return 'YawPitchRoll'

    def data_format(self):
        return '{:0.2f},{:0.2f},{:0.2f}'

    def column_header(self):
        return 'Yaw (degrees),Pitch (degrees),Roll (degrees)'

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        accel = converted[0].data
        mag = converted[1].data
        roll, pitch, yaw = roll_pitch_yaw(accel, mag)
        yaw = apply_declination(degrees(yaw), self.declination)
        yaw = reshape(yaw, (1, -1))
        data = vstack((yaw, degrees(pitch), degrees(roll)))
        self.output_stream.write(self.stream_name(), data, converted[0].time)
