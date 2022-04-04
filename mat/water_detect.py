MAX_INT16 = 65535


class WaterDetect:
    def __init__(self):
        pass

    def convert(self, raw_value):
        return round((raw_value/MAX_INT16)*100)
