from numpy import (
    array,
    dot,
)
from mat.meter import Meter
from mat.utils import array_from_tags


class CubicMagnetometer(Meter):
    HARD_IRON_KEYS = ['MXV', 'MYV', 'MZV']
    SOFT_X_KEYS = ['MXX', 'MXY', 'MXZ']
    SOFT_Y_KEYS = ['MYX', 'MYY', 'MYZ']
    SOFT_Z_KEYS = ['MZX', 'MZY', 'MZZ']

    def __init__(self, hs):
        self.hard_iron = array_from_tags(hs, self.HARD_IRON_KEYS)
        self.soft_iron = array_from_tags(hs,
                                         self.SOFT_X_KEYS,
                                         self.SOFT_Y_KEYS,
                                         self.SOFT_Z_KEYS)

    def convert(self, raw_magnetometer, temperature=None):
        return dot(self.soft_iron, raw_magnetometer + self.hard_iron)
