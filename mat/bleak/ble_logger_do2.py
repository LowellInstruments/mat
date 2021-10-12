import queue

from tendo import singleton
from mat.bleak.ble_engine_do2 import ble_engine_do2
from mat.bleak.ble_logger import BLELogger


class BLELoggerDO2(BLELogger):
    def __init__(self):
        self.connected = False
        singleton.SingleInstance()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = ble_engine_do2(self.q1, self.q2)
        self.th.start()
