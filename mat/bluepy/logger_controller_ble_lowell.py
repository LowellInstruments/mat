from datetime import datetime
import json
import math
from mat.logger_controller import LoggerController, STATUS_CMD, TIME_CMD, FIRMWARE_VERSION_CMD, SD_FREE_SPACE_CMD, \
    DO_SENSOR_READINGS_CMD, SET_TIME_CMD, LOGGER_INFO_CMD, DIR_CMD, DEL_FILE_CMD, LOGGER_INFO_CMD_W, LOGGER_HSA_CMD_W, \
    CALIBRATION_CMD, RESET_CMD, RUN_CMD, RWS_CMD, STOP_CMD, SWS_CMD, REQ_FILE_NAME_CMD
from mat.bluepy.logger_controller_ble_lowell_utils import *
from mat.utils import is_valid_mac_address


class LoggerControllerBLELowell(LoggerController):

    def __init__(self, mac, h=0):
        self.mac = mac
        self.h = h
        assert is_valid_mac_address(mac)
        super().__init__(mac)
        self.per = None
        self.svc = None
        self.cha = None
        self.dlg = LCBLELowellDelegate()

    def open(self) -> bool:
        return ble_connect_lowell_logger(self)

    def close(self) -> bool:
        try:
            self.per.disconnect()
            self.per = None
            return True
        except AttributeError:
            return False

    def _ble_write(self, data, response=False):
        assert len(data) <= MTU_SIZE
        self.cha.write(data, withResponse=response)

    def _ble_ans(self, tag) -> bytes:
        assert tag not in (DWG_FILE_CMD, DWL_CMD)
        self.dlg.buf = bytes()
        last = 0
        t = ble_ans_calc_t(tag)
        while 1:
            now = time.perf_counter()
            if self.per.waitForNotifications(.01):
                # print(self.dlg.buf)
                t += .01
                last = now
                continue
            if now > t:
                # final timeout
                break
            if last and now > last + .5:
                # timeout: received too long ago
                break
        return self.dlg.buf

    def _ble_cmd(self, *args) -> bytes:  # pragma: no cover
        """ cmd: 'STS', a: [b'STS', b'020X'] """

        to_send, tag = ble_cmd_build(*args)
        self._ble_write(to_send.encode())
        a = self._ble_ans(tag)
        return a

    def command(self, *args) -> bytes:
        return self._ble_cmd(*args)

    # --------------------
    # Lowell API commands
    # --------------------

    def ble_get_mtu(self) -> int:
        return int(self.per.status()['mtu'][0])

    def ble_cmd_gtm(self) -> datetime:
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
            # depending on version
            '0202': 'delayed'
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
            # a: b'UPT 0812345678'
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

    def ble_cmd_led(self) -> str:
        a = self._ble_cmd(LED_CMD)
        return 'ok' if a == b'LED 00' else 'error'

    def ble_cmd_stm(self) -> str:
        fmt = '%Y/%m/%d %H:%M:%S'
        s = datetime.now().strftime(fmt)
        a = self._ble_cmd(SET_TIME_CMD, s)
        return 'ok' if a == b'STM 00' else 'error'

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

    def ble_cmd_tst(self) -> str:
        a = self._ble_cmd(TEST_CMD)
        return 'ok' if a == b'TST 00' else 'error'

    def ble_cmd_mts(self) -> str:
        a = self._ble_cmd(MY_TOOL_SET_CMD, 'SN')
        return 'ok' if a == b'MTS 00' else 'error'

    def ble_cmd_frm(self) -> bool:
        a = self._ble_cmd(FORMAT_CMD)
        rv = a == b'FRM 00'
        time.sleep(1)
        return rv

    # utility function
    def _ble_cmd_file_list(self) -> list:
        rv = []
        for i in range(5):
            rv = self._ble_cmd(DIR_CMD)
            if rv:
                break
            print('BLE: DIR empty, retry {} of 5'.format(i))
            time.sleep(2)

        # e.g. [b'.', b'0', b'..', b'0', b'do2_dummy.lid', b'123', b'\x04']
        return rv

    def ble_cmd_dir_ext(self, ext) -> dict:  # pragma: no cover
        file_list = self._ble_cmd_file_list()
        return ble_file_list_as_dict(file_list, ext, match=True)

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

    def ble_cmd_whs(self, data) -> str:
        valid = ['TMO', 'TMR', 'TMA', 'TMB', 'TMC']
        assert data[:3] in valid
        a = self._ble_cmd(LOGGER_HSA_CMD_W, 'TMO12345')
        return 'ok' if a == b'WHS 00' else 'error'

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

    def ble_cmd_rst(self) -> str:
        a = self._ble_cmd(RESET_CMD)
        return 'ok' if a == b'RST 00' else 'error'

    def ble_cmd_cfg(self, cfg_d) -> bool:
        assert type(cfg_d) is dict
        s = json.dumps(cfg_d)
        a = self._ble_cmd(CONFIG_CMD, s)
        return a == b'CFG 00'

    def ble_cmd_run(self) -> str:
        a = self._ble_cmd(RUN_CMD)
        return 'ok' if a == b'RUN 00' else 'error'

    def ble_cmd_rws(self, s) -> str:
        a = self._ble_cmd(RWS_CMD, s)
        return 'ok' if a == b'RWS 00' else 'error'

    def ble_cmd_stp(self) -> str:
        a = self._ble_cmd(STOP_CMD)
        v = (b'STP 00', b'STP 0200')
        return 'ok' if a in v else 'error'

    def ble_cmd_sws(self, s) -> str:
        a = self._ble_cmd(SWS_CMD, s)
        return 'ok' if a == b'SWS 00' else 'error'

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

    def ble_cmd_dwl(self, file_size, sig=None) -> bytes:
        # do not remove this, in case buffer has 'DWG 00'
        self.dlg.buf = bytes()
        data_file = bytes()
        number_of_chunks = math.ceil(file_size / 2048)
        for i in range(number_of_chunks):
            timeout, data_chunk = self._dwl_chunk(i)
            data_file += data_chunk
            if sig:
                sig.emit()

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

    def ble_cmd_slw_ensure(self, v: str):
        assert v in ('on', 'off')
        rv = self.ble_cmd_slw()
        if rv in ['error', v]:
            return rv
        rv = self.ble_cmd_slw()
        return 'error' if rv != v else rv

    def ble_cmd_wak_ensure(self, v: str):
        assert v in ('on', 'off')
        rv = self.ble_cmd_wak()
        if rv in ['error', v]:
            return rv
        rv = self.ble_cmd_wak()
        return 'error' if rv != v else rv
