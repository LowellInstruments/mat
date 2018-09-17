

ACCEL_MAG = ['Accelerometer', 'Magnetometer']


def output_factory(sensors, parameters):
    outputters = []
    remaining_sensors = [s.name for s in sensors]

    # Special cases first
    for class_ in [Current, Compass, AccelerometerMagnetometer]:
        if class_.OUTPUT_TYPE == parameters['output_type']:
            this_output = _get_outputers(class_,
                                         sensors,
                                         class_.REQUIRED_SENSORS)

            remaining_sensors = _remove_from_list(remaining_sensors,
                                                  class_.REQUIRED_SENSORS)
            outputters.append(this_output)
            break  # there can be only one special case

    # Convert remaining sensors as discrete channels
    for sensor_name in remaining_sensors:
        required_sensors = _sensors_from_names(sensors, sensor_name)
        this_output = DiscreteChannels(required_sensors)
        outputters.append(this_output)

    return outputters


def _get_outputers(class_, sensors, sensor_names):
    required_sensors = _sensors_from_names(sensors, sensor_names)
    return class_(required_sensors)


def _sensors_from_names(sensors, names):
    return [s for s in sensors if s.name in names]


def _remove_from_list(source_list, items_to_remove):
    return [x for x in source_list if x not in items_to_remove]


class Outputter:
    def __init__(self):
        self.output_obj = None
        self.data_product = None

    def output_page(self, data_page):
        pass


class OutputObj:
    """
    Accept data sensors and provide
    """
    pass


class CsvFile(OutputObj):
    OUTPUT_FORMAT = 'csv'
    pass


class HdfFile(OutputObj):
    OUTPUT_FORMAT = 'hdf5'
    pass


class DiscreteChannels:
    OUTPUT_TYPE = ''
    REQUIRED_SENSORS = []

    def __init__(self, sensors):
        self.sensors = sensors

    def convert_page(self):
        pass


class AccelerometerMagnetometer(DiscreteChannels):
    REQUIRED_SENSORS = ['Accelerometer', 'Magnetometer']

    def convert_page(self):
        pass


class Current(AccelerometerMagnetometer):
    OUTPUT_TYPE = 'current'

    def convert_page(self):
        pass


class Compass(AccelerometerMagnetometer):
    OUTPUT_TYPE = 'compass'

    def convert_page(self):
        pass
