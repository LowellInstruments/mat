import platform
import queue
from tendo import singleton
from mat.bleak.ble_engine_do2_dummy import ble_engine_do2_dummy
from mat.bleak.ble_logger_do2 import BLELogger
from mat.bleak.ble_utils_logger_do2_dummy import MAC_LOGGER_DO2_DUMMY


class BLELoggerDO2Dummy(BLELogger):

    def __init__(self):
        super(BLELoggerDO2Dummy).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = ble_engine_do2_dummy(self.q1, self.q2)
        self.th.start()

    def ble_connect(self, mac):
        mac = MAC_LOGGER_DO2_DUMMY
        if platform.system() == 'Windows':
            mac = mac.upper()
        self.connected = True
        return mac

    def ble_scan(self):
        return [MAC_LOGGER_DO2_DUMMY]

    def ble_disconnect(self):
        self.connected = False
        return b'disconnect OK'


