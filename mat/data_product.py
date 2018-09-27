from os import path
from mat.output_stream import output_stream_factory
import numpy as np
from abc import ABC, abstractmethod


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
    if len(requested_sensors) < len(names):
        raise ValueError('Required sensor not in sensors')
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
        data, time = self.sensors[0].convert(data_page,
                                             self.average,
                                             page_time)
        self.output_stream.write(self.sensors[0].name, data, time)


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
        accel, time = self.sensors[0].convert(data_page,
                                              self.average,
                                              page_time)
        mag, _ = self.sensors[1].convert(data_page,
                                         self.average,
                                         page_time)
        data = np.vstack((accel, mag))
        self.output_stream.write(self.stream_name(), data, time)


class Current(DataProduct):
    OUTPUT_TYPE = 'current'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def stream_name(self):
        pass  # pragma: no cover

    def data_format(self):
        pass  # pragma: no cover

    def header_string(self):
        pass  # pragma: no cover

    def process_page(self, data_page, page_time):
        pass  # pragma: no cover


class Compass(DataProduct):
    OUTPUT_TYPE = 'compass'
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def stream_name(self):
        return 'Compass'

    def data_format(self):
        return '{:0.1f}'

    def header_string(self):
        return 'Bearing (deg)'

    def process_page(self, data_page, page_time):
        pass  # pragma: no cover
