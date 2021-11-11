import time

from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.bluepy.logger_controller_ble_rn4020_utils import ble_connect_rn4020_logger
from mat.bluepy.xmodem_rn4020 import ble_xmd_get_file_rn4020


class LoggerControllerBLERN4020(LoggerControllerBLELowell):  # pragma: no cover

    def open(self):
        return ble_connect_rn4020_logger(self)

    def _ble_write(self, data, response=False):
        b = [data[i:i + 1] for i in range(len(data))]
        for _ in b:
            self.cha.write(_, withResponse=response)

    def ble_write(self, data, response=False):
        # only used at xmodem
        return self._ble_write(data, response)

    def _ble_cmd(self, *args):  # pragma: no cover
        # RN4020 answers have \r\n and \r\n
        a = super()._ble_cmd(*args)
        a = a[2:] if a and a.startswith(b'\n\r') else a
        a = a[:-2] if a and a.endswith(b'\r\n') else a
        return a

    def ble_cmd_dwg(self, name) -> bool:  # pragma: no cover
        # does not exist for RN4020 loggers
        return False

    def get_file(self, lc, name, size, p=None) -> bool:  # pragma: no cover
        self.dlg.buf = bytes()
        cmd = 'GET {:02x}{}\r'.format(len(name), name)
        lc.ble_write(cmd.encode())
        till = time.perf_counter() + 5
        to_dl = False
        while 1:
            lc.per.waitForNotifications(.1)
            if time.perf_counter() > till:
                break
            _ = lc.dlg.buf.decode().strip()
            if _ == 'GET 00':
                to_dl = True
                break

        dl = False
        if to_dl:
            # file-system based progress indicator
            if p:
                f = open(p, 'w+')
                f.write(str(0))
                f.close()
            dl = ble_xmd_get_file_rn4020(lc, size, p)
        return dl
