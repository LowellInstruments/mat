import platform
import queue
import threading
from mat.ble.ble_macs import MAC_LOGGER_DO2_DUMMY
from mat.ble.bleak_beta.logger_do2 import LoggerBLE
from mat.ble.bleak_beta.engine_do2_dummy import engine_do2_dummy


class LoggerDO2Dummy(LoggerBLE):
    def __init__(self):
        super(LoggerDO2Dummy).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = threading.Thread(target=engine_do2_dummy, args=(self.q1, self.q2,))
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


