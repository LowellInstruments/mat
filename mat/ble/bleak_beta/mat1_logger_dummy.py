import queue
import threading
from mat.ble.bleak_beta.ble_logger_do2 import BLELogger
from mat.ble.bleak_beta.mat1_engine import engine_mat1
from mat.ble.bleak_beta.mat1_logger import BLELoggerMAT1


class BLELoggerMAT1Dummy(BLELogger):

    def __init__(self):
        super(BLELoggerMAT1).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = threading.Thread(target=engine_mat1, args=(self.q1, self.q2,))
        self.th.start()
