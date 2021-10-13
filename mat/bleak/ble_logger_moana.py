import queue

from tendo import singleton

from mat.bleak.ble_engine_moana import ble_engine_moana
from mat.bleak.ble_logger_do2 import BLELogger
from mat.bleak.ble_engine_mat1 import ble_engine_mat1
from mat.bleak.ble_utils_logger_mat1 import ble_cmd_dir_result_as_dict_rn4020
from mat.logger_controller import DIR_CMD


class BLELoggerMoana:

    def __init__(self):
        self.connected = False
        singleton.SingleInstance()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = ble_engine_moana(self.q1, self.q2)
        self.th.start()

    def _cmd(self, c):
        print('\t<- (lc) {}'.format(c))
        self.q1.put(c)
        a = self.q2.get()
        print('\t-> (lc) {}'.format(a))
        return a

    # todo: copy the rest from bluepy moana

    def ble_cmd_auth(self):
        c = '*EA123'
        return self._cmd(c)
