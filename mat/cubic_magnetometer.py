from numpy import (
    array,
    dot,
)
from mat.meter import Meter
from mat.utils import array_from_tags


HARD_IRON_KEYS = ['MXV', 'MYV', 'MZV']
SOFT_X_KEYS = ['MXX', 'MXY', 'MXZ']
SOFT_Y_KEYS = ['MYX', 'MYY', 'MYZ']
SOFT_Z_KEYS = ['MZX', 'MZY', 'MZZ']
OFFSET_KEYS = ['AXV', 'AYV', 'AZV']
CUBIC_KEYS = ['AXC', 'AYC', 'AZC']
SHARED_KEYS = set(CUBIC_KEYS).union(SOFT_X_KEYS,
                                    SOFT_Y_KEYS,
                                    SOFT_Z_KEYS,
                                    OFFSET_KEYS)


class CubicMagnetometer(Meter):
    REQUIRED_KEYS = set(SHARED_KEYS).union(HARD_IRON_KEYS)
    def __init__(self, hs):
        self.hard_iron = array_from_tags(hs, HARD_IRON_KEYS)
        self.soft_iron = array_from_tags(hs,
                                         SOFT_X_KEYS,
                                         SOFT_Y_KEYS,
                                         SOFT_Z_KEYS)

    def convert(self, raw_magnetometer, temperature=None):
        return dot(self.soft_iron, raw_magnetometer + self.hard_iron)
