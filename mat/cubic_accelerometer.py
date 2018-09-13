from numpy import (
    array,
    dot,
)
from mat.meter import Meter


class CubicAccelerometer(Meter):
    keys = {'AXX', 'AXY', 'AXZ',
            'AYX', 'AYY', 'AYZ',
            'AZX', 'AZY', 'AZZ'}

    def __init__(self, hs):
        self.gain = array([[hs['AXX'], hs['AXY'], hs['AXZ']],
                           [hs['AYX'], hs['AYY'], hs['AYZ']],
                           [hs['AZX'], hs['AZY'], hs['AZZ']]])
        self.offset = array([[hs['AXV']], [hs['AYV']], [hs['AZV']]])
        self.cubic = array([[hs['AXC']], [hs['AYC']], [hs['AZC']]])

    def convert(self, raw_meter, temperature=None):
        raw_accelerometer = raw_meter / 1024.
        return (dot(self.gain, raw_accelerometer) +
                self.offset +
                self.cubic * raw_accelerometer ** 3)
