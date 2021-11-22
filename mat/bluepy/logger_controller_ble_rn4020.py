import time
from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.bluepy.logger_controller_ble_rn4020_utils import ble_connect_rn4020_logger
from mat.bluepy.xmodem_rn4020 import ble_xmd_get_file_rn4020
from mat.logger_controller import SWS_CMD, SENSOR_READINGS_CMD
from mat.logger_controller_ble_cmd import BTC_CMD


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

    def ble_cmd_btc(self) -> bool:
        c = 'BTC 00T,0006,0000,0064\r'
        self._ble_write(c.encode())
        a = self._ble_ans(BTC_CMD)
        time.sleep(.1)
        return a == b'\n\rCMD\r\nAOK\r\nMLDP\r\n'

    def ble_cmd_dwg(self, name) -> bool:  # pragma: no cover
        # does not exist for RN4020 loggers
        return False

    def ble_cmd_dir(self) -> dict:
        # 'DIR' on RN4020 is picky
        time.sleep(1)
        rv = self.ble_cmd_dir_ext('*')
        return rv

    def ble_cmd_bat(self):
        a = self._ble_cmd(SENSOR_READINGS_CMD)

        # bat as hex string, little endian
        bh = '0000'
        if a and len(a.split()) == 2:
            # a: b'GSR 2811...99'
            _ = a.split()[1].decode()[2:]
            bh = _[28:32]
            bh = bh[-2:] + bh[:2]

        bat = int(bh, 16)
        return bat

    def ble_cmd_sws(self, s):
        # slightly different than newer loggers
        a = self._ble_cmd(SWS_CMD, s)
        return a == b'SWS 0200'

    def ble_cmd_get(self, name, size, p=None) -> bytes:  # pragma: no cover

        # file-system based download percentage indicator
        if p:
            f = open(p, 'w+')
            f.write(str(0))
            f.close()

        # real download
        self.dlg.buf = bytes()
        cmd = 'GET {:02x}{}\r'.format(len(name), name)
        self.ble_write(cmd.encode())
        till = time.perf_counter() + 5
        while 1:
            self.per.waitForNotifications(.1)
            if time.perf_counter() > till:
                return bytes()
            _ = self.dlg.buf.decode().strip()
            if _ == 'GET 00':
                break

        return ble_xmd_get_file_rn4020(self, size, p)

    def ble_cmd_ping(self) -> bool:
        # ensure a RN4020-based logger is there
        for i in range(5):
            rv = self.ble_cmd_sts()
            if rv in ('running', 'stopped', 'delayed'):
                return True
            time.sleep(1)
        return False

