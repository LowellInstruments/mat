from os import path
from mat.output_stream import output_stream_factory


def data_product_factory(sensors, parameters):
    """
    Instantiate a data product subclass and pass it the necessary sensors
    """
    data_products = []

    # Special cases first
    for class_ in [Current, Compass, AccelerometerMagnetometer]:
        if class_.OUTPUT_TYPE == parameters['output_type']:
            required_sensors = _sensor_from_name(sensors,
                                                 class_.REQUIRED_SENSORS)
            data_product = class_(required_sensors, parameters)
            sensors = [s for s in sensors if s not in required_sensors]

            data_products.append(data_product)
            break  # there can be only one special case

    # Convert remaining sensors as discrete channels
    for sensor in sensors:
        data_product = DiscreteChannel(sensor, parameters)
        data_products.append(data_product)

    return data_products


def _sensor_from_name(sensors, names):
    # TODO throw an error if a sensor is missing
    return [s for s in sensors if s.name in names]


class DataProduct:
    OUTPUT_TYPE = ''
    REQUIRED_SENSORS = []

    def __init__(self, sensors, parameters):
        self.sensors = sensors
        self.parameters = parameters
        filename = path.basename(parameters['path'])
        dir_name = path.dirname(parameters['path'])
        destination = parameters['output_directory'] or dir_name
        self.output_stream = output_stream_factory(parameters['output_format'],
                                                   filename,
                                                   destination)
        self.configure_output_stream()

    def configure_output_stream(self):
        pass  # pragma: no cover

    def process_page(self, data_page, page_time):
        pass  # pragma: no cover


class DiscreteChannel(DataProduct):
    OUTPUT_TYPE = ''
    REQUIRED_SENSORS = []

    def configure_output_stream(self):
        name = self.sensors.name
        self.output_stream.add_stream(name)
        self.output_stream.set_data_format(name, self.sensors.spec.format)
        self.output_stream.set_header_string(name, self.sensors.spec.header)
        self.output_stream.set_time_format(name,
                                           self.parameters['time_format'])
        self.output_stream.write_header(name)

    def process_page(self, data_page, page_time):
        raw_data = self.sensors.parse(data_page)
        data = self.sensors.apply_calibration(raw_data)
        time = page_time + self.sensors.sample_times()
        self.output_stream.write(self.sensors.name, time, data)


class AccelerometerMagnetometer(DiscreteChannel):
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def file_suffix(self):
        return '_AccelMag'

    def process_page(self, data_page, page_time):
        pass


class Current(AccelerometerMagnetometer):
    OUTPUT_TYPE = 'current'

    def file_suffix(self):
        return '_Current'

    def process_page(self, data_page, page_time):
        pass


class Compass(AccelerometerMagnetometer):
    OUTPUT_TYPE = 'compass'

    def file_suffix(self):
        return '_Compass'

    def process_page(self, data_page, page_time):
        pass
