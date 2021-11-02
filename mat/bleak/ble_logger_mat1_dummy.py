import platform
import queue
from tendo import singleton
from mat.bleak.ble_engine_do2_dummy import ble_engine_do2_dummy
from mat.bleak.ble_logger_do2 import BLELogger
from mat.bleak.ble_utils_logger_do2_dummy import MAC_LOGGER_DO2_DUMMY


class BLELoggerMAT1Dummy(BLELogger):

    def __init__(self):
        super(BLELoggerMAT1Dummy).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        #self.th = ble_engine_mat1_dummy(self.q1, self.q2)
        self.th.start()
