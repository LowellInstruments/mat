import time
from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
from mat.ble.bluepy.rn4020_utils import connect_rn4020
from mat.ble.bluepy.rn4020_xmodem import rn4020_xmodem_get_file
from mat.logger_controller_ble import *
from mat.logger_controller import STATUS_CMD, TIME_CMD, \
    SET_TIME_CMD, LOGGER_INFO_CMD_W, \
    RUN_CMD, RWS_CMD, STOP_CMD, SWS_CMD, DIR_CMD, SENSOR_READINGS_CMD, DEL_FILE_CMD


class LoggerControllerRN4020(LoggerControllerCC26X2R):  # pragma: no cover

    def open(self):
        return connect_rn4020(self)

    def _ble_write(self, data, response=False):
        b = [data[i:i + 1] for i in range(len(data))]
        for _ in b:
            self.cha.write(_, withResponse=response)

    def ble_write(self, data, response=False):
        # only used at xmodem
        return self._ble_write(data, response)

    def _ble_cmd(self, *args):  # pragma: no cover
        # call PARENT's _ble_cmd() function
        a = super()._ble_cmd(*args)
        # adjust RN4020 answer prefixes & suffixes
        a = a[2:] if a and a.startswith(b'\n\r') else a
        a = a[2:] if a and a.startswith(b'\r\n') else a
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

        # battery as hex string, little endian
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

        # separate any previous unwanted stuff
        time.sleep(1)

        # real download
        self.dlg.buf = bytes()
        cmd = 'GET {:02x}{}\r'.format(len(name), name)
        self.ble_write(cmd.encode())
        till = time.perf_counter() + 20
        while 1:
            self.per.waitForNotifications(.01)
            if time.perf_counter() > till:
                return bytes()
            _ = self.dlg.buf.decode().strip()
            if _ == 'GET 00':
                break

        return rn4020_xmodem_get_file(self, size, p)

    def ble_cmd_ping(self) -> bool:
        # ensure a RN4020-based logger is there
        for i in range(5):
            rv = self.ble_cmd_sts()
            if rv in ('running', 'stopped', 'delayed'):
                return True
            time.sleep(1)
        return False

    def _answer_complete(self, tag):
        v = self.dlg.buf
        if not v:
            return
        n = len(v)

        # prefix and suffix of RN4020
        te = b'\n\r' + tag.encode()

        if v == b'ERR':
            return True

        if tag == RUN_CMD:
            return v.startswith(te) and n == 10
        if tag == STOP_CMD:
            # b'\n\rSTP 0200\r\n'
            return v.startswith(te) and n == 12
        if tag == RWS_CMD:
            # RN4020 does not has RWS
            time.sleep(1)
            assert False
        if tag == SWS_CMD:
            return v.startswith(te) and n == 12
        if tag == SET_TIME_CMD:
            return v.endswith(b'STM 00\r\n')
        if tag == LOGGER_INFO_CMD_W:
            return v.endswith(b'WLI 00\r\n')
        if tag == STATUS_CMD:
            return v.startswith(te) and n == 12
        if tag == TIME_CMD:
            return v.startswith(te) and n == 29
        if tag == SENSOR_READINGS_CMD:
            return len(v) == 38 + 4 or len(v) == 46 + 4
        if tag == DEL_FILE_CMD:
            return v.endswith(b'DEL 00\r\n')
        if tag == BTC_CMD:
            return v.endswith(b'\n\rCMD\r\nAOK\r\nMLDP\r\n')
        if tag == DIR_CMD:
            return v.endswith(b'\x04\n\r') or v.endswith(b'\x04')