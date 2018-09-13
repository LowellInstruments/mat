from numpy import (
    array,
    dot,
)
from mat.meter import Meter
from mat.utils import array_from_tags


class CubicAccelerometer(Meter):
    X_KEYS = ['AXX', 'AXY', 'AXZ']
    Y_KEYS = ['AYX', 'AYY', 'AYZ']
    Z_KEYS = ['AZX', 'AZY', 'AZZ']
    REQUIRED_KEYS = set(X_KEYS).union(Y_KEYS).union(Z_KEYS)
    OFFSET_KEYS = ['AXV', 'AYV', 'AZV']
    CUBIC_KEYS = ['AXC', 'AYC', 'AZC']

    def __init__(self, hs):
        self.gain = array_from_tags(hs, self.X_KEYS, self.Y_KEYS, self.Z_KEYS)
        self.offset = array_from_tags(hs, self.OFFSET_KEYS)
        self.cubic = array_from_tags(hs, self.CUBIC_KEYS)

    def convert(self, raw_meter, temperature=None):
        raw_accelerometer = raw_meter / 1024.
        return (dot(self.gain, raw_accelerometer) +
                self.offset +
                self.cubic * raw_accelerometer ** 3)
