import platform
import queue
from tendo import singleton
from mat.bleak.ble_engine import ENGINE_CMD_CON
from mat.bleak.ble_engine_do2_dummy import ble_engine_do2_dummy
from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.bleak.ble_logger_do2_utils_dummy import MAC_LOGGER_DO2_DUMMY


class BLELoggerDO2Dummy(BLELoggerDO2):

    def __init__(self):
        self.connected = False
        singleton.SingleInstance()
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


