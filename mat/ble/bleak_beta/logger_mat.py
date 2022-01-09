import queue
import threading
from mat.ble.bleak_beta.logger_do2 import LoggerBLE
from mat.ble.bleak_beta.engine_mat import engine_mat
from mat.ble_utils_shared import xmd_frame_check_crc
from mat.logger_controller import DIR_CMD
from mat.logger_controller_ble import GET_FILE_CMD
from mat.utils import lowell_file_list_as_dict


class LoggerMAT(LoggerBLE):

    def __init__(self):
        super().__init__()
        self.q1 = queue.Queue()
        self.q2 = queue.Queue()
        self.th = threading.Thread(target=engine_mat, args=(self.q1, self.q2,))
        self.th.start()

    def ble_cmd_btc(self):
        c = self._cmd_build('BTC 00T,0006,0000,0064')
        return self._cmd(c)

    def ble_cmd_dir(self):
        c = self._cmd_build(DIR_CMD)
        rv = self._cmd(c)
        return lowell_file_list_as_dict(rv, ext='*')

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
