import queue
from mat.ble.bleak_beta.ble_logger_do2 import BLELogger


class BLELoggerMAT1Dummy(BLELogger):

    def __init__(self):
        super(BLELoggerMAT1Dummy).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        #self.th = ble_engine_mat1_dummy(self.q1, self.q2)
        self.th.start()
