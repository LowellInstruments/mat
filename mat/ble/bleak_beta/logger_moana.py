import platform
import queue
import time
from tendo import singleton
from mat.ble.bleak_beta.engine_base_utils import ENGINE_CMD_DISC, ENGINE_CMD_SCAN, ENGINE_CMD_CON, ENGINE_CMD_BYE
from mat.ble.bleak_beta.engine_moana import engine_moana


class LoggerMoana:

    def __init__(self):
        self.connected = False
        singleton.SingleInstance()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = engine_moana(self.q1, self.q2)
        self.th.start()

    def _cmd(self, c):
        print('\t<- (lc) {}'.format(c))
        self.q1.put(c)
        a = self.q2.get()
        print('\t-> (lc) {}'.format(a))
        return a

    def ble_bye(self):
        c = '{}'.format(ENGINE_CMD_BYE)
        return self._cmd(c)

    def ble_scan(self):
        c = '{}'.format(ENGINE_CMD_SCAN)
        return self._cmd(c)

    def ble_disconnect(self):
        c = '{}'.format(ENGINE_CMD_DISC)
        self.connected = False
        return self._cmd(c)

    def close(self):
        return self.ble_disconnect()

    def ble_connect(self, mac):
        if platform.system() == 'Windows':
            mac = mac.upper()
        c = '{} {}'.format(ENGINE_CMD_CON, mac)
        rv = self._cmd(c)
        self.connected = rv == mac
        return rv

    def ble_cmd_auth(self):
        c = '*EA123'
        return self._cmd(c)

    def ble_cmd_time_sync(self):
        epoch_s = str(int(time.time()))
        c = '*LT{}'.format(epoch_s)
        return self._cmd(c)

    def ble_cmd_file_info(self):
        c = '*BF'
        return self._cmd(c)
