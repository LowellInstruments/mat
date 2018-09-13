from numpy import (
    array,
    dot,
)
from mat.meter import Meter


class CubicMagnetometer(Meter):
    def __init__(self, hs):
        self.hard_iron = array([[hs['MXV']], [hs['MYV']], [hs['MZV']]])
        self.soft_iron = array([[hs['MXX'], hs['MXY'], hs['MXZ']],
                                [hs['MYX'], hs['MYY'], hs['MYZ']],
                                [hs['MZX'], hs['MZY'], hs['MZZ']]])

    def convert(self, raw_magnetometer, temperature=None):
        return dot(self.soft_iron, raw_magnetometer + self.hard_iron)
