from numpy import array
from mat.meter import Meter


class LinearAccelerometer(Meter):
    offset_keys = ['AXA', 'AYA', 'AZA']
    slope_keys = ['AXB', 'AYB', 'AZB']
    
    keys = set(offset_keys).union(slope_keys)

    def __init__(self, hs):
        self.slope = array([[1 / hs['AXB']],
                            [1 / hs['AYB']],
                            [1 / hs['AZB']]])
        self.offset = array([[hs['AXA']], [hs['AYA']], [hs['AZA']]])

    def convert(self, raw_meter, temperature=None):
        return -raw_meter * self.slope - self.offset
