from os import path
from mat.output_stream import output_stream_factory
import numpy as np
from abc import ABC, abstractmethod
from mat.utils import roll_pitch_yaw


def data_product_factory(sensors, parameters):
    """
    Instantiate a data product subclass and pass it the necessary sensors
    """
    data_products = []
    output_stream = _create_output_stream(parameters)
    parameters = _accel_mag_check(sensors, parameters)

    # Special cases first
    for class_ in [Current, Compass, AccelMag]:
        if class_.OUTPUT_TYPE == parameters['output_type']:
            required_sensors = _sensor_from_name(sensors,
                                                 class_.REQUIRED_SENSORS)
            sensors = remove_sensors(sensors, required_sensors)
            data_product = class_(required_sensors, parameters, output_stream)
            data_products.append(data_product)

    # Convert remaining sensors as discrete channels
    for sensor in sensors:
        data_product = DiscreteChannel([sensor], parameters, output_stream)
        data_products.append(data_product)
    return data_products


def _accel_mag_check(sensors, parameters):
    sensor_names = [s.name for s in sensors]
    if parameters['output_type'] == 'discrete':
        if set(AccelMag.REQUIRED_SENSORS).issubset(sensor_names):
            parameters['output_type'] = 'accelmag'
    return parameters


def remove_sensors(sensors, sensors_to_remove):
    return [s for s in sensors if s not in sensors_to_remove]


def _sensor_from_name(sensors, names):
    if not set(names).issubset([s.name for s in sensors]):
        raise ValueError('Requested sensors not active')
    requested_sensors = [s for s in sensors if s.name in names]
    return requested_sensors


def _create_output_stream(parameters):
    filename = path.basename(parameters['path'])
    dir_name = path.dirname(parameters['path'])
    destination = parameters['output_directory'] or dir_name
    return output_stream_factory(parameters['output_format'],
                                 filename,
                                 destination,
                                 parameters['time_format'])


class DataProduct(ABC):
    OUTPUT_TYPE = ''
    REQUIRED_SENSORS = []

    def __init__(self, sensors, parameters, output_stream):
        self.sensors = sensors
        self.parameters = parameters
        self.output_stream = output_stream
        self.average = parameters['average']
        self.configure_output_stream()

    def configure_output_stream(self):
        name = self.stream_name()
        self.output_stream.add_stream(name)
        self.output_stream.set_data_format(name, self.data_format())
        self.output_stream.set_header_string(name, self.header_string())
        self.output_stream.write_header(name)

    def convert_sensors(self, data_page, page_time):
        converted = []
        for sensor in self.sensors:
            data, time = sensor.convert(data_page, self.average, page_time)
            converted.append((data, time))
        return converted

    @abstractmethod
    def stream_name(self):
        pass  # pragma: no cover

    @abstractmethod
    def data_format(self):
        pass  # pragma: no cover

    @abstractmethod
    def header_string(self):
        pass  # pragma: no cover

    @abstractmethod
    def process_page(self, data_page, page_time):
        pass  # pragma: no cover

    def _join_spec_fields(self, field):
        fields = [getattr(x.sensor_spec, field) for x in self.sensors]
        return ','.join(fields)


class DiscreteChannel(DataProduct):
    OUTPUT_TYPE = 'discrete'
    REQUIRED_SENSORS = []

    def stream_name(self):
        return self.sensors[0].name

    def data_format(self):
        return self.sensors[0].sensor_spec.format

    def header_string(self):
        return self.sensors[0].sensor_spec.header

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        self.output_stream.write(self.sensors[0].name,
                                 converted[0][0],
                                 converted[0][1])


class AccelMag(DataProduct):
    OUTPUT_TYPE = 'accelmag'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def stream_name(self):
        return 'AccelMag'

    def data_format(self):
        return self._join_spec_fields('format')

    def header_string(self):
        return self._join_spec_fields('header')

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        data = np.vstack((converted[0][0], converted[1][0]))
        self.output_stream.write(self.stream_name(), data, converted[0][1])


class Current(DataProduct):
    OUTPUT_TYPE = 'current'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def __init__(self, sensors, parameters, output_stream):
        super().__init__(sensors, parameters, output_stream)
        self.tilt_curve = self.parameters['tilt_curve']
        self.declination = self.parameters.get('declination') or 0

    def stream_name(self):
        return 'Current'

    def data_format(self):
        return '{:0.2f},{:0.2f},{:0.2f},{:0.2f}'

    def header_string(self):
        return ('Speed (cm/s),'
                'Bearing (degrees),'
                'Velocity-N (cm/s),'
                'Velocity-E (cm/s)')

    def _calc_tilt__and_bearing(self, accel, mag):
        roll, pitch, yaw = roll_pitch_yaw(accel, mag)
        x = -np.cos(roll) * np.sin(pitch)
        y = np.sin(roll)

        tilt = np.arccos(
            accel[2] / np.sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2))
        is_usd = tilt > np.pi / 2
        tilt[is_usd] = np.pi - tilt[is_usd]

        bearing = np.arctan2(y, x) + yaw
        bearing = np.mod(bearing + np.deg2rad(self.declination), 2 * np.pi)
        return tilt, bearing

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        accel = converted[0][0]
        mag = converted[1][0]
        tilt, bearing = self._calc_tilt__and_bearing(accel, mag)
        speed = self.tilt_curve.speed_from_tilt(np.degrees(tilt))

        velocity_n = speed * np.cos(bearing)
        velocity_e = speed * np.sin(bearing)

        data = np.vstack((speed, bearing, velocity_n, velocity_e))

        self.output_stream.write(self.stream_name(), data, converted[0][1])


class Compass(DataProduct):
    OUTPUT_TYPE = 'compass'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def __init__(self, sensors, parameters, output_stream):
        super().__init__(sensors, parameters, output_stream)
        self.declination = self.parameters.get('declination') or 0

    def stream_name(self):
        return 'Compass'

    def data_format(self):
        return '{:0.1f}'

    def header_string(self):
        return 'Bearing (deg)'

    def process_page(self, data_page, page_time):
        converted = self.convert_sensors(data_page, page_time)
        accel = converted[0][0]
        mag = converted[1][0]
        m = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]])
        accel = np.dot(m, accel)
        mag = np.dot(m, mag)
        roll, pitch, heading = roll_pitch_yaw(accel, mag)
        heading = np.rad2deg(heading)
        heading = np.mod(heading + self.declination, 360)
        heading = np.reshape(heading, (1, -1))
        self.output_stream.write(self.stream_name(), heading, converted[0][1])
