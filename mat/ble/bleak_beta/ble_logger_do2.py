import queue
from mat.ble.bleak_beta.ble_engine_do2 import ble_engine_do2
from mat.ble.bleak_beta.ble_logger import BLELogger


class BLELoggerDO2(BLELogger):
    def __init__(self):
        super(BLELoggerDO2).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = ble_engine_do2(self.q1, self.q2)
        self.th.start()
