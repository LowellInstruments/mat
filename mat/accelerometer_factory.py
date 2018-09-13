from mat.cubic_accelerometer import CubicAccelerometer
from mat.linear_accelerometer import LinearAccelerometer
from mat.utils import obj_from_coefficients



ACC_KEYS_FOR_CLASS = [
    (CubicAccelerometer.REQUIRED_KEYS, CubicAccelerometer),
    (LinearAccelerometer.REQUIRED_KEYS, LinearAccelerometer),
]


def accelerometer_factory(calibration):
    return obj_from_coefficients(calibration.coefficients,
                                 ACC_KEYS_FOR_CLASS)
