from mat.cubic_accelerometer import CubicAccelerometer
from mat.linear_accelerometer import LinearAccelerometer
from mat.utils import obj_from_coefficients



CUBIC_ACC_KEYS = {'AXX', 'AXY', 'AXZ',
                  'AYX', 'AYY', 'AYZ',
                  'AZX', 'AZY', 'AZZ'}

ACC_KEYS_FOR_CLASS = [
    (CubicAccelerometer.keys, CubicAccelerometer),
    (LinearAccelerometer.keys, LinearAccelerometer),
]


def accelerometer_factory(calibration):
    return obj_from_coefficients(calibration.coefficients,
                                 ACC_KEYS_FOR_CLASS)
