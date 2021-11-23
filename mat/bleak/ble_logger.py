import datetime
import json
import math
import platform
import time
from abc import ABC, abstractmethod

from mat.bleak.ble_utils_engine import ENGINE_CMD_BYE, ENGINE_CMD_DISC, ENGINE_CMD_CON, ENGINE_CMD_SCAN, ENGINE_CMD_EXC
from mat.logger_controller_ble_cmd import *
from mat.bleak.ble_utils_logger_do2 import ble_cmd_dir_result_as_dict
from mat.bluepy.xmlrpc_lc_ble_client import XS_BLE_EXC_LC
from mat.logger_controller import (
    STATUS_CMD,
    FIRMWARE_VERSION_CMD,
    DIR_CMD,
    TIME_CMD,
    SET_TIME_CMD,
    CALIBRATION_CMD,
    LOGGER_HSA_CMD_W,
    LOGGER_INFO_CMD_W,
    LOGGER_INFO_CMD,
    STOP_CMD,
    SWS_CMD,
    DEL_FILE_CMD, SD_FREE_SPACE_CMD, RUN_CMD
)
from tendo import singleton


class BLELogger(ABC):
    @abstractmethod
    def __init__(self):
        # these are defined in subclasses
        self.connected = False
        singleton.SingleInstance()
        self.q1 = None
        self.q2 = None
        self.th = None

    @staticmethod
    def _cmd_build(c, p='') -> str:
        # 'CMD' / 'par' -> 'CMD 03par\r'
        n = '{:02x}'.format(len(p)) if p else ''
        return '{} {}{}\r'.format(c, n, p)

    def _cmd(self, c):
        print('\t<- (lc) {}'.format(c))
        self.q1.put(c)
        a = self.q2.get()
        if not c.startswith('DWL'):
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

    def ble_cmd_sts(self):
        c = self._cmd_build(STATUS_CMD)
        return self._cmd(c)

    def ble_cmd_gfv(self):
        c = self._cmd_build(FIRMWARE_VERSION_CMD)
        return self._cmd(c)

    def ble_cmd_dir(self):
        c = self._cmd_build(DIR_CMD)
        b = self._cmd(c)
        return ble_cmd_dir_result_as_dict(b)

    def ble_cmd_dwg(self, s):
        c = self._cmd_build(DWG_FILE_CMD, s)
        return self._cmd(c)

    def ble_cmd_stm(self):
        fmt = '%Y/%m/%d %H:%M:%S'
        s = datetime.datetime.now().strftime(fmt)
        c = self._cmd_build(SET_TIME_CMD, s)
        return self._cmd(c)

    def ble_cmd_stp(self):
        c = self._cmd_build(STOP_CMD)
        return self._cmd(c)

    def ble_cmd_run(self):
        c = self._cmd_build(RUN_CMD)
        return self._cmd(c)

    def ble_cmd_led(self):
        c = self._cmd_build(LED_CMD)
        return self._cmd(c)

    def ble_cmd_gdo(self):
        c = self._cmd_build(OXYGEN_SENSOR_CMD)
        a = self._cmd(c)
        dos, dop, dot = '', '', ''
        if a and len(a.split()) == 2:
            # a: b'GDO 0c112233445566'
            _ = a.split()[1].decode()
            dos, dop, dot = _[2:6], _[6:10], _[10:14]
            dos = dos[-2:] + dos[:2]
            dop = dop[-2:] + dop[:2]
            dot = dot[-2:] + dot[:2]
        return dos, dop, dot

    def ble_cmd_gtm(self):
        c = self._cmd_build(TIME_CMD)
        return self._cmd(c)

    def ble_cmd_dwl(self, size, sig=None):  # pragma: no cover
        # chunk by chunk
        a = bytes()
        n = math.ceil(size / 2048)
        start = time.perf_counter()
        for i in range(n):
            if sig:
                x1 = math.ceil(100 * i * 2048 / size)
                sig.emit(x1)
            c = self._cmd_build(DWL_CMD, str(i))
            ch = self._cmd(c)
            a += ch if ch else bytes()
            # print(len(ch))

        print(len(a))
        rv = None if not a or (len(a) < size) else a[:size]
        if rv:
            end = time.perf_counter()
            speed = size / (end - start)
            print('speed {} KB/s'.format(speed / 1000))
        return rv

    def ble_cmd_frm(self):
        c = self._cmd_build(FORMAT_CMD)
        return self._cmd(c)

    def ble_cmd_bat(self) -> int:
        c = self._cmd_build(BAT_CMD)
        a = self._cmd(c)
        # a: b'BAT 047D08'
        if not a:
            return 0xFFFF
        mv = a.split()[1].decode()
        mv = mv[-2:] + mv[-4:-2]
        print('\t0x{} == {} mV'.format(mv, int(mv, 16)))
        return a

    def ble_cmd_cfg(self, cfg_d: dict):
        s = json.dumps(cfg_d)
        c = self._cmd_build(CONFIG_CMD, s)
        return self._cmd(c)

    def ble_cmd_mts(self):
        c = self._cmd_build(MY_TOOL_SET_CMD)
        _ = time.perf_counter()
        rv = self._cmd(c)
        t = time.perf_counter() - _
        print('mts took {:.2} seconds'.format(t))
        return rv

    def ble_cmd_log(self):
        c = self._cmd_build(LOG_EN_CMD)
        return self._cmd(c)

    def ble_cmd_wak(self):
        c = self._cmd_build(WAKE_CMD)
        return self._cmd(c)

    def ble_cmd_wli(self, s):
        c = self._cmd_build(LOGGER_INFO_CMD_W, s)
        return self._cmd(c)

    def ble_cmd_rli(self):
        a = []
        c = self._cmd_build(LOGGER_INFO_CMD, 'SN')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(LOGGER_INFO_CMD, 'CA')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(LOGGER_INFO_CMD, 'BA')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(LOGGER_INFO_CMD, 'MA')
        rv = self._cmd(c)
        a.append(rv)
        return a

    def ble_cmd_whs(self, s):
        c = self._cmd_build(LOGGER_HSA_CMD_W, s)
        return self._cmd(c)

    def ble_cmd_rhs(self):
        a = []
        c = self._cmd_build(CALIBRATION_CMD, 'TMO')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(CALIBRATION_CMD, 'TMA')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(CALIBRATION_CMD, 'TMB')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(CALIBRATION_CMD, 'TMC')
        rv = self._cmd(c)
        a.append(rv)
        c = self._cmd_build(CALIBRATION_CMD, 'TMR')
        rv = self._cmd(c)
        a.append(rv)
        return a

    def ble_cmd_sws(self, s):
        c = self._cmd_build(SWS_CMD, s)
        return self._cmd(c)

    def ble_cmd_crc(self, s):
        # be safe and wait w/ CRC
        time.sleep(2)
        c = self._cmd_build(CRC_CMD, s)
        return self._cmd(c)

    def ble_cmd_slw(self):
        c = self._cmd_build(SLOW_DWL_CMD)
        return self._cmd(c)

    def ble_cmd_ensure_slw_on(self):
        a = self.ble_cmd_slw()
        if a.decode()[-1] == '1':
            return 'OK'
        a = self.ble_cmd_slw()
        if a.decode()[-1] == '1':
            return 'OK'

    def ble_cmd_ensure_slw_off(self):
        a = self.ble_cmd_slw()
        if a.decode()[-1] == '0':
            return 'OK'
        a = self.ble_cmd_slw()
        if a.decode()[-1] == '0':
            return 'OK'

    def ble_cmd_mbl(self):
        c = self._cmd_build(MOBILE_CMD)
        return self._cmd(c)

    def ble_cmd_siz(self, s):
        c = self._cmd_build(SIZ_CMD, s)
        return self._cmd(c)

    def ble_cmd_sri(self):
        c = self._cmd_build(GET_SENSOR_INTERVAL)
        return self._cmd(c)

    def ble_cmd_mci(self):
        c = self._cmd_build(GET_COMMON_SENSOR_INTERVAL)
        return self._cmd(c)

    def ble_cmd_dri(self):
        c = self._cmd_build(GET_SENSOR_DO_INTERVAL)
        return self._cmd(c)

    def ble_cmd_del(self, s):
        c = self._cmd_build(DEL_FILE_CMD, s)
        return self._cmd(c)

    def ble_cmd_cfs(self):
        c = self._cmd_build(SD_FREE_SPACE_CMD)
        return self._cmd(c)

    def ble_cmd_exc_engine(self):
        # special command for testing engine exceptions
        c = self._cmd_build(ENGINE_CMD_EXC)
        return self._cmd(c)

    def ble_cmd_exc_lc(self):
        # special command for testing my exceptions
        self.q1.put(XS_BLE_EXC_LC)
        return XS_BLE_EXC_LC
