import queue
from mat.bleak.ble_logger_do2 import BLELogger
from mat.bleak.ble_engine_mat1 import ble_engine_mat1
from mat.bleak.ble_utils_logger_mat1 import ble_cmd_dir_result_as_dict_rn4020
from mat.logger_controller import DIR_CMD


class BLELoggerMAT1(BLELogger):

    def __init__(self):
        super(BLELoggerMAT1).__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = ble_engine_mat1(self.q1, self.q2)
        self.th.start()

    def ble_cmd_btc(self):
        c = self._cmd_build('BTC 00T,0006,0000,0064')
        return self._cmd(c)

    def ble_cmd_dir(self):
        c = self._cmd_build(DIR_CMD)
        rv = self._cmd(c)
        return ble_cmd_dir_result_as_dict_rn4020(rv)
