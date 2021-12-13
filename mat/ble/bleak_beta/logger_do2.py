import queue
import threading
from mat.ble.bleak_beta.engine_do2 import engine_do2
from mat.ble.bleak_beta.logger_ble import LoggerBLE


class LoggerDO2(LoggerBLE):
    def __init__(self):
        super(LoggerDO2).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = threading.Thread(target=engine_do2, args=(self.q1, self.q2,))
        self.th.start()
