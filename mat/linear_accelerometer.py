from numpy import array
from mat.meter import Meter
from mat.utils import array_from_tags


class LinearAccelerometer(Meter):
    OFFSET_KEYS = ['AXA', 'AYA', 'AZA']
    SLOPE_KEYS = ['AXB', 'AYB', 'AZB']
    
    REQUIRED_KEYS = set(OFFSET_KEYS).union(SLOPE_KEYS)

    def __init__(self, hs):
        self.slope = array([[1 / hs['AXB']],
                            [1 / hs['AYB']],
                            [1 / hs['AZB']]])
        self.offset = array_from_tags(hs, self.OFFSET_KEYS)

    def convert(self, raw_meter, temperature=None):
        return -raw_meter * self.slope - self.offset
