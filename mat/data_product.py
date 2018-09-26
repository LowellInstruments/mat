from os import path
from mat.output_stream import output_stream_factory
import numpy as np
from abc import ABC, abstractmethod


def data_product_factory(sensors, parameters):
    """
    Instantiate a data product subclass and pass it the necessary sensors
    """
    data_products = []

    # Special cases first
    for class_ in [Current, Compass]:
        if class_.OUTPUT_TYPE == parameters['output_type']:
            # there should be an exception of this fails
            required_sensors = _sensor_from_name(sensors,
                                                 class_.REQUIRED_SENSORS)
            sensors = remove_sensors(sensors, required_sensors)
            data_product = class_(required_sensors, parameters)

            data_products.append(data_product)
            break  # there can be only one special case

    try:
        required_sensors = _sensor_from_name(sensors,
                                             AccelMag.REQUIRED_SENSORS)
        sensors = remove_sensors(sensors, required_sensors)
        data_product = AccelMag(required_sensors, parameters)
        data_products.append(data_product)
    except ValueError:
        pass

    # Convert remaining sensors as discrete channels
    for sensor in sensors:
        data_product = DiscreteChannel([sensor], parameters)
        data_products.append(data_product)

    return data_products


def remove_sensors(sensors, sensors_to_remove):
    return [s for s in sensors if s not in sensors_to_remove]


def _sensor_from_name(sensors, names):
    requested_sensors = [s for s in sensors if s.name in names]
    if len(requested_sensors) < len(names):
        raise ValueError('Required sensor not in sensors')
    return requested_sensors


class DataProduct(ABC):
    OUTPUT_TYPE = ''
    REQUIRED_SENSORS = []

    def __init__(self, sensors, parameters):
        # TODO I think I can just pass in output_format instead of parameters
        self.sensors = sensors
        self.parameters = parameters
        filename = path.basename(parameters['path'])
        dir_name = path.dirname(parameters['path'])
        destination = parameters['output_directory'] or dir_name
        self.output_stream = output_stream_factory(parameters['output_format'],
                                                   filename,
                                                   destination)
        self.average = parameters['average']
        self.configure_output_stream()

    def configure_output_stream(self):
        name = self.stream_name()
        self.output_stream.add_stream(name)
        self.output_stream.set_time_format(name,
                                           self.parameters['time_format'])
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

    def convert_sensors(self, data_page, page_time):
        converted = []
        for i, sensor in enumerate(self.sensors):
            raw_data, time = sensor.parse_page(data_page, average=True)
            time += page_time
            data = self.converters[i].convert(raw_data)
            converted.append((data, time))
        return converted


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
    OUTPUT_TYPE = 'discrete'
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


# def calc_compass(accel, mag, declination=0):
#     # The channels need to be adjusted because compass mode has the logger horizontal, not vertical like current
#     m = np.array([[0, 0, 1], [0, -1, 0], [1, 0, 0]])
#     accel = np.dot(m, accel)
#     mag = np.dot(m, mag)
#
#     roll = np.arctan2(accel[1], accel[2])
#     pitch = np.arctan2(-accel[0], accel[1] * np.sin(roll) + accel[2] * np.cos(roll))
#     by = mag[2] * np.sin(roll) - mag[1] * np.cos(roll)
#     bx = mag[1] * np.cos(pitch) + mag[1] * np.sin(pitch) * np.sin(roll) + mag[2] * np.sin(pitch) * np.cos(roll)
#
#     heading = np.arctan2(by, bx)
#     heading = np.rad2deg(heading)
#     heading = np.mod(heading + declination, 360)
#     return heading

# class Steve(DataProduct):
#     OUTPUT_TYPE = 'steve'
#     REQUIRED_SENSORS = ['Accelerometer']
#
#     def configure_output_stream(self):
#         self.name = 'TiltVibe'
#         self.output_stream.add_stream(self.name)
#         data_format = '{:0.2f},{:0.5f}'
#         self.output_stream.set_data_format(self.name, data_format)
#         header = 'Tilt (degrees),Stddev (m/s^2)'
#         self.output_stream.set_header_string(self.name, header)
#         self.output_stream.set_time_format(self.name,
#                                            self.parameters['time_format'])
#         self.output_stream.write_header(self.name)
#
#     def process_page(self, data_page, page_time):
#         raw_data = self.sensors[0].parse(data_page)
#         data = self.sensors[0].apply_calibration(raw_data)
#         time = page_time + self.sensors[0].sample_times()[::3]
#         time = time[0::30*64]
#         vec_sum = (data[0,:]**2 + data[1,:]**2 + data[2,:]**2)**0.5
#         extra_cols = len(vec_sum) % (30*64)
#         if extra_cols:
#             vec_sum = vec_sum[:-extra_cols]
#         vec_sum2 = np.reshape(vec_sum, (-1, 64*30))
#         std_dev = np.std(vec_sum2, axis=1)
#
#         tilt = tilt_from_accel(data)
#         if extra_cols:
#             tilt = tilt[:-extra_cols]
#         tilt = np.reshape(tilt, (-1, 64*30))
#         tilt = np.mean(tilt, axis=1)
#
#         out_data = np.vstack((tilt, std_dev))
#         self.output_stream.write(self.name, time, out_data)
#
#
# def tilt_from_accel(accel):
#     tilt = np.arccos(
#         accel[2] / np.sqrt(accel[0] ** 2 + accel[1] ** 2 + accel[2] ** 2))
#     return np.degrees(tilt)
