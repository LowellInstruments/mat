
class WaterDetect:
    def __init__(self, hs=None):
        pass

    def convert(self, mv):
        # 100% water is 3000 mV == VCC
        vcc = 3000
        return ((mv / vcc) * 100).round()
