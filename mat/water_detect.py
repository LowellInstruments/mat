import math


class WaterDetect:
    def __init__(self, hs=None):
        pass

    def convert(self, mV):
        # 100% water is 3000 mV == VCC
        vcc = 3000

        # prevent 100% in data file
        return math.floor((mV / vcc) * 100)
