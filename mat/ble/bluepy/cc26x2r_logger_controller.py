import time
from datetime import datetime, timezone
import json
import math
from mat.ble.bluepy.cc26x2r_utils import LCBLELowellDelegate, connect_cc26x2r, MTU_SIZE, \
    calculate_answer_timeout, build_command
from mat.logger_controller import LoggerController, STATUS_CMD, TIME_CMD, FIRMWARE_VERSION_CMD, SD_FREE_SPACE_CMD, \
    DO_SENSOR_READINGS_CMD, SET_TIME_CMD, LOGGER_INFO_CMD, DEL_FILE_CMD, LOGGER_INFO_CMD_W, LOGGER_HSA_CMD_W, \
    CALIBRATION_CMD, RESET_CMD, RUN_CMD, RWS_CMD, STOP_CMD, SWS_CMD, REQ_FILE_NAME_CMD, DIR_CMD, SENSOR_READINGS_CMD
from mat.logger_controller_ble import *
from mat.utils import is_valid_mac_address, lowell_file_list_as_dict


class LoggerControllerCC26X2R(LoggerController):

    def __init__(self, mac, h=0, what=''):
        self.mac = mac
        self.h = h
        assert is_valid_mac_address(mac)
        super().__init__(mac)
        self.per = None
        self.svc = None
        self.cha = None
        self.dlg = LCBLELowellDelegate()
        # any note you want to keep track of
        self.what = what

    def open(self) -> bool:
        return connect_cc26x2r(self)

    def close(self) -> bool:
        rv = False
        try:
            self.per.disconnect()
            self.per = None
            rv = True
        except AttributeError:
            pass
        finally:
            self.per = None
            return rv

    def _ble_write(self, data, response=False):
        assert len(data) <= MTU_SIZE
        self.cha.write(data, withResponse=response)

    def _ble_ans(self, tag) -> bytes:
        assert tag not in (DWG_FILE_CMD, DWL_CMD)
        self.dlg.buf = bytes()
        till = calculate_answer_timeout(tag)

        while 1:
            # reduce timeout when we received once
            if self.per.waitForNotifications(.01):
                till = time.perf_counter() + 3
                continue

            # timeout fully expired
            if time.perf_counter() > till:
                e = 'timeout -> tag {} -> {}'
                print(e.format(tag, self.dlg.buf))
                break

            # no more wait needed
            if self._answer_complete(tag):
                break

        return self.dlg.buf

    def _ble_cmd(self, *args) -> bytes:  # pragma: no cover
        """ cmd: 'STS', a: [b'STS', b'020X'] """

        to_send, tag = build_command(*args)
        self._ble_write(to_send.encode())
        return self._ble_ans(tag)

    def command(self, *args) -> bytes:
        return self._ble_cmd(*args)

    # --------------------
    # Lowell API commands
    # --------------------

    def ble_get_mtu(self) -> int:
        return int(self.per.status()['mtu'][0])

    def ble_cmd_btc(self):
        # cc26x2r does not have BTC command
        assert False

    def ble_cmd_gtm(self) -> datetime:
        # remember -> logger's time is UTC
        rv = self._ble_cmd(TIME_CMD)
        if len(rv) == 25:
            # rv: b'GTM 132000/01/01 01:44:49'
            rv = rv.decode()[6:]
            dt = datetime.strptime(rv, '%Y/%m/%d %H:%M:%S')
            return dt

    def ble_cmd_sts(self) -> str:
        a = self._ble_cmd(STATUS_CMD)
        _ = {
            '0200': 'running',
            '0201': 'stopped',
            '0203': 'delayed',
            # depending on version 'delayed' has 2
            '0202': 'delayed',
            '0209': 'matcfg_error'
        }
        # a: b'STS 0201'
        if a and len(a.split()) == 2:
            return _[a.split()[1].decode()]
        return 'error'

    def ble_cmd_gfv(self) -> str:
        a = self._ble_cmd(FIRMWARE_VERSION_CMD)
        if a and len(a.split()) == 2:
            return a.split()[1].decode()[2:]
        return 'error'

    def ble_cmd_bat(self) -> int:
        a = self._ble_cmd(BAT_CMD)
        if a and len(a.split()) == 2:
            # a: b'BAT 044E08'
            _ = a.split()[1].decode()
            b = _[-2:] + _[:2]
            return int(b, 16)
        return 0

    def ble_cmd_utm(self) -> int:
        a = self._ble_cmd(UP_TIME_CMD)
        if a and len(a.split()) == 2:
            # a: b'UTM 0812345678'
            print(a)
            _ = a.split()[1].decode()
            b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
            return int(b, 16)
        return 0

    def ble_cmd_cfs(self) -> float:
        a = self._ble_cmd(SD_FREE_SPACE_CMD)
        if a and len(a.split()) == 2:
            # a: b'CFS 0812345678'
            _ = a.split()[1].decode()
            b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
            free_bytes = int(b, 16)
            free_mb = free_bytes / 1024 / 1024
            return free_mb
        return 0

    def ble_cmd_gdo(self) -> (str, str, str):
        a = self._ble_cmd(DO_SENSOR_READINGS_CMD)
        dos, dop, dot = '', '', ''

        if a and len(a.split()) == 2:
            # a: b'GDO 0c112233445566'
            _ = a.split()[1].decode()
            dos, dop, dot = _[2:6], _[6:10], _[10:14]
            dos = dos[-2:] + dos[:2]
            dop = dop[-2:] + dop[:2]
            dot = dot[-2:] + dot[:2]
        return dos, dop, dot

    def ble_cmd_log(self) -> str:
        a = self._ble_cmd(LOG_EN_CMD)
        _ = {b'LOG 0201': 'on', b'LOG 0200': 'off'}
        return _.get(a, 'error')

    def ble_cmd_wak(self) -> str:
        a = self._ble_cmd(WAKE_CMD)
        _ = {b'WAK 0201': 'on', b'WAK 0200': 'off'}
        return _.get(a, 'error')

    def ble_cmd_slw(self) -> str:
        a = self._ble_cmd(SLOW_DWL_CMD)
        _ = {b'SLW 0201': 'on', b'SLW 0200': 'off'}
        return _.get(a, 'error')

    def ble_cmd_mbl(self) -> str:
        a = self._ble_cmd(MOBILE_CMD)
        _ = {b'MBL 0201': 'on', b'MBL 0200': 'off'}
        return _.get(a, 'error')

    def ble_cmd_led(self) -> bool:
        a = self._ble_cmd(LED_CMD)
        return a == b'LED 00'

    def ble_cmd_stm(self) -> bool:
        # time() -> seconds since epoch, in UTC
        # src: www.tutorialspoint.com/python/time_time.htm
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        fmt = '%Y/%m/%d %H:%M:%S'
        s = dt.strftime(fmt)
        print(s)
        # s: 2021/12/01 16:33:16
        a = self._ble_cmd(SET_TIME_CMD, s)
        return a == b'STM 00'

    def ble_cmd_gsn(self) -> str:
        a = self._ble_cmd(LOGGER_INFO_CMD, 'SN')
        if a and len(a.split()) == 2:
            return a.split()[1].decode()[2:]
        return 'error'

    def ble_cmd_ebr(self) -> str:
        a = self._ble_cmd(ERROR_WHEN_BOOT_OR_RUN_CMD, 'SN')
        if a and len(a.split()) == 2:
            return a.split()[1].decode()[2:]
        return 'error'

    def ble_cmd_tst(self) -> bool:
        a = self._ble_cmd(TEST_CMD)
        return a == b'TST 00'

    def ble_cmd_mts(self) -> bool:
        a = self._ble_cmd(MY_TOOL_SET_CMD, 'SN')
        return a == b'MTS 00'

    def ble_cmd_frm(self) -> bool:
        a = self._ble_cmd(FORMAT_CMD)
        time.sleep(1)
        return a == b'FRM 00'

    def ble_cmd_dir_ext(self, ext) -> dict:  # pragma: no cover
        # todo > check why sometimes no \x04
        f_l = self._ble_cmd(DIR_CMD)
        return lowell_file_list_as_dict(f_l, ext, match=True)

    def ble_cmd_dir(self) -> dict:  # pragma: no cover
        rv = self.ble_cmd_dir_ext('*')
        return rv

    def ble_cmd_del(self, file_name: str) -> bool:
        a = self._ble_cmd(DEL_FILE_CMD, file_name)
        return a == b'DEL 00'

    def ble_cmd_crc(self, file_name: str) -> str:
        a = self._ble_cmd(CRC_CMD, file_name)
        if a and len(a.split()) == 2:
            return a.split()[1].decode()[2:]
        return 'error'

    def ble_cmd_wli(self, info) -> str:
        # info: 'SN1234567
        valid = ['SN', 'BA', 'CA', 'MA']
        assert info[:2] in valid
        a = self._ble_cmd(LOGGER_INFO_CMD_W, info)
        return 'ok' if a == b'WLI 00' else 'error'

    def ble_cmd_rli(self) -> dict:
        info = {}
        a = self._ble_cmd(LOGGER_INFO_CMD, 'SN')
        if a and len(a.split()) == 2:
            info['SN'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(LOGGER_INFO_CMD, 'MA')
        if a and len(a.split()) == 2:
            info['MA'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(LOGGER_INFO_CMD, 'BA')
        if a and len(a.split()) == 2:
            info['BA'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(LOGGER_INFO_CMD, 'CA')
        if a and len(a.split()) == 2:
            info['CA'] = a.split()[1].decode()[2:]
        return info

    def ble_cmd_whs(self, data) -> bool:
        valid = ['TMO', 'TMR', 'TMA', 'TMB', 'TMC']
        assert data[:3] in valid
        a = self._ble_cmd(LOGGER_HSA_CMD_W, 'TMO12345')
        return a == b'WHS 00'

    def ble_cmd_rhs(self) -> dict:
        hsa = {}
        a = self._ble_cmd(CALIBRATION_CMD, 'TMO')
        if a and len(a.split()) == 2:
            hsa['TMO'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(CALIBRATION_CMD, 'TMR')
        if a and len(a.split()) == 2:
            hsa['TMR'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(CALIBRATION_CMD, 'TMA')
        if a and len(a.split()) == 2:
            hsa['TMA'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(CALIBRATION_CMD, 'TMB')
        if a and len(a.split()) == 2:
            hsa['TMB'] = a.split()[1].decode()[2:]
        a = self._ble_cmd(CALIBRATION_CMD, 'TMC')
        if a and len(a.split()) == 2:
            hsa['TMC'] = a.split()[1].decode()[2:]
        return hsa

    def ble_cmd_siz(self, file_name) -> int:
        a = self._ble_cmd(SIZ_CMD, file_name)
        if a and len(a.split()) == 2:
            i = int(a.split()[1].decode()[2:])
            return i
        return 0

    def ble_cmd_rst(self) -> bool:
        a = self._ble_cmd(RESET_CMD)
        return a == b'RST 00'

    def ble_cmd_cfg(self, cfg_d) -> bool:
        assert type(cfg_d) is dict
        s = json.dumps(cfg_d)
        a = self._ble_cmd(CONFIG_CMD, s)
        return a == b'CFG 00'

    def ble_cmd_run(self) -> bool:
        a = self._ble_cmd(RUN_CMD)
        return a == b'RUN 00'

    def ble_cmd_rws(self, s) -> bool:
        a = self._ble_cmd(RWS_CMD, s)
        return a == b'RWS 00'

    def ble_cmd_stp(self) -> bool:
        a = self._ble_cmd(STOP_CMD)
        v = (b'STP 00', b'STP 0200')
        return a in v

    def ble_cmd_sws(self, s) -> bool:
        a = self._ble_cmd(SWS_CMD, s)
        return a == b'SWS 00'

    def ble_cmd_rfn(self) -> str:
        a = self._ble_cmd(REQ_FILE_NAME_CMD)
        if a == b'RFN 00':
            return ''
        if a and len(a.split()) == 2:
            return a.split()[1].decode()[2:]
        return 'error'

    def _dwl_chunk(self, chunk_number) -> tuple:
        # send DWL command
        c_n = chunk_number
        cmd = 'DWL {:02x}{}\r'.format(len(str(c_n)), c_n)
        self._ble_write(cmd.encode())

        # receive DWL answer
        timeout = False
        data = bytes()
        last = time.perf_counter()
        while 1:
            # keep accumulating BLE notifications
            if self.per.waitForNotifications(.1):
                last = time.perf_counter()

            # timeout == last fragment (good) or error (bad)
            if time.perf_counter() > last + 2:
                data += self.dlg.buf
                timeout = True
                break

            # got 1 entire chunk, use >= because of race conditions
            if len(self.dlg.buf) >= 2048:
                data += self.dlg.buf[:2048]
                self.dlg.buf = self.dlg.buf[2048:]
                break

        return timeout, data

    def ble_cmd_dwl(self, file_size, p=None) -> bytes:
        # do not remove this, in case buffer has 'DWG 00'
        self.dlg.buf = bytes()
        data_file = bytes()
        number_of_chunks = math.ceil(file_size / 2048)

        # file-system based progress indicator
        if p:
            f = open(p, 'w+')
            f.write(str(0))
            f.close()

        # download and update file w/ progress
        for i in range(number_of_chunks):
            timeout, data_chunk = self._dwl_chunk(i)
            data_file += data_chunk
            if p:
                f = open(p, 'w+')
                _ = len(data_file) / file_size * 100
                _ = _ if _ < 100 else 100
                f.write(str(_))
                f.close()

        # truncate and return
        self.dlg.buf = bytes()
        if len(data_file) < file_size:
            return bytes()
        data_file = data_file[:file_size]
        return data_file

    def ble_cmd_dwg(self, name) -> bool:  # pragma: no cover
        """ see if a file can be DWG-ed """

        self.dlg.buf = bytes()
        _ = '{} {:02x}{}\r'
        cmd = _.format(DWG_FILE_CMD, len(name), name)
        self._ble_write(cmd.encode())
        self.per.waitForNotifications(5)
        return self.dlg.buf == b'DWG 00'

    def ble_cmd_slw_ensure(self, v: str) -> bool:
        assert v in ('on', 'off')
        rv = self.ble_cmd_slw()
        if rv == v:
            return True
        rv = self.ble_cmd_slw()
        if rv == v:
            return True
        return False

    def ble_cmd_wak_ensure(self, v: str) -> bool:
        assert v in ('on', 'off')
        rv = self.ble_cmd_wak()
        if rv == v:
            return True
        rv = self.ble_cmd_wak()
        if rv == v:
            return True
        return False

    def _answer_complete(self, tag):
        v = self.dlg.buf
        if not v:
            return
        n = len(v)
        te = tag.encode()

        if v == b'ERR':
            return True

        if tag == RUN_CMD:
            return v == b'RUN 00'
        if tag == STOP_CMD:
            return v == b'STP 00'
        if tag == RWS_CMD:
            return v == b'RWS 00'
        if tag == SWS_CMD:
            return v == b'SWS 00'
        if tag == SET_TIME_CMD:
            return v == b'STM 00'
        if tag == LOGGER_INFO_CMD_W:
            return v == b'WLI 00'
        if tag == STATUS_CMD:
            return v.startswith(te) and n == 8
        if tag == BAT_CMD:
            return v.startswith(te) and n == 10
        if tag == TIME_CMD:
            return v.startswith(te) and n == 25
        if tag in SLOW_DWL_CMD:
            return v.startswith(te) and n == 8
        if tag in WAKE_CMD:
            return v.startswith(te) and n == 8
        if tag == CRC_CMD:
            return v.startswith(te) and n == 14
        if tag == FORMAT_CMD:
            return v == b'FRM 00'
        if tag == CONFIG_CMD:
            return v == b'CFG 00'
        if tag == DO_SENSOR_READINGS_CMD:
            return v.startswith(te) and n == 18
        # todo > test this one
        if tag == DIR_CMD:
            return v.endswith(b'\x04')
        if tag == SENSOR_READINGS_CMD:
            return len(v) == 32 + 6 or len(v) == 40 + 6
