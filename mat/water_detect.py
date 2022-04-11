MAX_INT16 = 65535


class WaterDetect:
    def __init__(self, hs=None):
        pass

    def convert(self, raw_value):
        return ((raw_value/MAX_INT16)*100).round()
