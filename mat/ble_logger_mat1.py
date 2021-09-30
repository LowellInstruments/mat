import queue
from tendo import singleton
from mat.ble_logger_do2 import BLELoggerDO2
from mat.ble_logger_mat1_engine import ble_engine_mat1
from mat.ble_logger_mat1_utils import ble_cmd_dir_result_as_dict_rn4020
from mat.logger_controller import DIR_CMD


class BLELoggerMAT1(BLELoggerDO2):
    def __init__(self, dummy=False):
        self.connected = False
        singleton.SingleInstance()
        # BLE engine in thread, command + answer queues
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        eng = ble_decide_engine_mat1(dummy)
        eng(self.q1, self.q2)

    # commands slightly different RN4020 vs cc26X2
    def ble_cmd_btc(self):
        c = self._cmd_build('BTC 00T,0006,0000,0064')
        return self._cmd(c)

    def ble_cmd_dir(self):
        c = self._cmd_build(DIR_CMD)
        rv = self._cmd(c)
        return ble_cmd_dir_result_as_dict_rn4020(rv)


def ble_decide_engine_mat1(dummy):
    # if dummy:
    #     return ble_engine_mat1_dummy
    return ble_engine_mat1
