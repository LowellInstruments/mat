from mat.cubic_magnetometer import CubicMagnetometer
from mat.temp_compensated_magnetometer import TempCompensatedMagnetometer
from mat.utils import obj_from_coefficients


MAG_KEYS_FOR_CLASS = [
    (TempCompensatedMagnetometer.REQUIRED_KEYS, TempCompensatedMagnetometer),
    (CubicMagnetometer.REQUIRED_KEYS, CubicMagnetometer),
]


def magnetometer_factory(calibration):
    return obj_from_coefficients(calibration.coefficients,
                                 MAG_KEYS_FOR_CLASS)
