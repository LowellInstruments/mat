from mat.cubic_magnetometer import CubicMagnetometer
from mat.temp_compensated_magnetometer import TempCompensatedMagnetometer
from mat.utils import obj_from_coefficients


TEMP_MAG_KEYS = {'MXX', 'MXY', 'MXZ',
                 'MYX', 'MYY', 'MYZ',
                 'MZX', 'MZY', 'MZZ',
                 'AXV', 'AYV', 'AZV',
                 'AXC', 'AYC', 'AZC',
                 'TMX', 'TMY', 'TMZ', 'MRF'}
CUBIC_MAG_KEYS = {'MXX', 'MXY', 'MXZ',
                  'MYX', 'MYY', 'MYZ',
                  'MZX', 'MZY', 'MZZ',
                  'AXV', 'AYV', 'AZV',
                  'AXC', 'AYC', 'AZC'}

MAG_KEYS_FOR_CLASS = [
    (TEMP_MAG_KEYS, TempCompensatedMagnetometer),
    (CUBIC_MAG_KEYS, CubicMagnetometer),
]


def magnetometer_factory(calibration):
    return obj_from_coefficients(calibration.coefficients,
                                 MAG_KEYS_FOR_CLASS)
