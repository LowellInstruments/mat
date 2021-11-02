import queue
from mat.bleak.ble_logger_do2 import BLELogger
from mat.bleak.ble_engine_mat1 import ble_engine_mat1
from mat.bleak.ble_utils_logger_mat1 import ble_cmd_dir_result_as_dict_rn4020
from mat.ble_utils_shared import xmd_frame_check_crc
from mat.logger_controller import DIR_CMD
from mat.logger_controller_ble_cmd import GET_FILE_CMD


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

    def ble_cmd_get(self, s):
        c = self._cmd_build(GET_FILE_CMD, s)
        return self._cmd(c)

    def ble_cmd_xmodem(self, size: int):
        data = bytes()
        c = b'XMD C'
        self.q1.put(c)
        a = self.q2.get()
        i = 0
        while 1:
            if len(a) != 1029:
                break

            rv = xmd_frame_check_crc(a)
            if not rv:
                break

            i += 1
            print('xmodem -> {}'.format(i))
            # lose xmodem header and crc
            data += a[3:-2]
            c = b'XMD \x06'
            self.q1.put(c)
            a = self.q2.get()

        # truncate
        if len(data) >= size:
            data = data[:size]
            return data
