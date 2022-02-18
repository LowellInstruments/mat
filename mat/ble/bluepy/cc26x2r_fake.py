import datetime
import time
from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
from mat.ble.bluepy.cc26x2r_utils import build_command, MTU_SIZE
from mat.logger_controller_ble import DWG_FILE_CMD, DWL_CMD
from mat.utils import is_valid_mac_address


class CC26X2RFake(LoggerControllerCC26X2R):

    def __init__(self, mac, h=0, what=''):
        self.mac = mac
        self.h = h
        self.connected = False
        assert is_valid_mac_address(mac)

    def open(self) -> bool:
        self.connected = True
        return self.connected

    def close(self) -> bool:
        self.connected = False
        return self.connected

    def _ble_write(self, data, response=False):
        assert self.connected
        # do nothing
        time.sleep(.1)

    def _ble_cmd(self, *args) -> bytes:  # pragma: no cover
        """ cmd: 'STS', a: [b'STS', b'020X'] """
        to_send, tag = build_command(*args)
        self._ble_write(to_send.encode())
        return self._ble_ans(tag)

    def _ble_ans(self, tag) -> bytes:
        assert tag not in (DWG_FILE_CMD, DWL_CMD)
        if tag == 'STS':
            return b'STS 0201'
        elif tag == 'GTM':
            a = datetime.datetime.now()
            a = a.strftime('%Y/%m/%d %H:%M:%S')
            return b'GTM 13' + a.encode()
        elif tag == 'GFV':
            return b'GFV 061.2.45'
        elif tag == 'BAT':
            return b'BAT 041209'
        elif tag == 'UTM':
            return b'UTM 0812345678'

    def command(self, *args) -> bytes:
        return self._ble_cmd(*args)

    # ------------------------------------------------
    # Lowell API commands different from real cc26x2r
    # ------------------------------------------------

    def ble_get_mtu(self) -> int:
        return MTU_SIZE

#     def ble_cmd_utm(self) -> int:
#         a = self._ble_cmd(UP_TIME_CMD)
#         if a and len(a.split()) == 2:
#             # a: b'UTM 0812345678'
#             print(a)
#             _ = a.split()[1].decode()
#             b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
#             return int(b, 16)
#         return 0
#
#     def ble_cmd_cfs(self) -> float:
#         a = self._ble_cmd(SD_FREE_SPACE_CMD)
#         if a and len(a.split()) == 2:
#             # a: b'CFS 0812345678'
#             _ = a.split()[1].decode()
#             b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
#             free_bytes = int(b, 16)
#             free_mb = free_bytes / 1024 / 1024
#             return free_mb
#         return 0
#
#     def ble_cmd_gdo(self) -> (str, str, str):
#         a = self._ble_cmd(DO_SENSOR_READINGS_CMD)
#         dos, dop, dot = '', '', ''
#
#         if a and len(a.split()) == 2:
#             # a: b'GDO 0c112233445566'
#             _ = a.split()[1].decode()
#             dos, dop, dot = _[2:6], _[6:10], _[10:14]
#             dos = dos[-2:] + dos[:2]
#             dop = dop[-2:] + dop[:2]
#             dot = dot[-2:] + dot[:2]
#             if dos == 'CCD0' or dop == 'CCD0' or dot == 'CCD0':
#                 print('error: check DO sensor connection')
#         return dos, dop, dot
#
#     def ble_cmd_gsr(self) -> int:
#         a = self._ble_cmd(SENSOR_READINGS_CMD)
#         tmp, prs, bat = '', '', ''
#         if a and len(a.split()) == 2:
#             # a: b'GSR 28...'
#             _ = a.split()[1].decode()
#             tmp = _[2+0:2+4]
#             prs = _[2+4:2+8]
#             bat = _[2+28:2+32]
#         return tmp, prs, bat
#
#     def ble_cmd_log(self) -> str:
#         a = self._ble_cmd(LOG_EN_CMD)
#         _ = {b'LOG 0201': 'on', b'LOG 0200': 'off'}
#         return _.get(a, 'error')
#
#     def ble_cmd_wak(self) -> str:
#         a = self._ble_cmd(WAKE_CMD)
#         _ = {b'WAK 0201': 'on', b'WAK 0200': 'off'}
#         return _.get(a, 'error')
#
#     def ble_cmd_mbl(self) -> str:
#         a = self._ble_cmd(MOBILE_CMD)
#         _ = {b'MBL 0201': 'on_1',
#              b'MBL 0202': 'on_2',
#              b'MBL 0200': 'off'}
#         return _.get(a, 'error')
#
#     def ble_cmd_led(self) -> bool:
#         a = self._ble_cmd(LED_CMD)
#         return a == b'LED 00'
#
#     def ble_cmd_stm(self) -> bool:
#         # time() -> seconds since epoch, in UTC
#         # src: www.tutorialspoint.com/python/time_time.htm
#         dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
#         fmt = '%Y/%m/%d %H:%M:%S'
#         s = dt.strftime(fmt)
#         # s: 2021/12/01 16:33:16
#         a = self._ble_cmd(SET_TIME_CMD, s)
#         return a == b'STM 00'
#
#     def ble_cmd_gsn(self) -> str:
#         a = self._ble_cmd(LOGGER_INFO_CMD, 'SN')
#         if a and len(a.split()) == 2:
#             return a.split()[1].decode()[2:]
#         return 'error'
#
#     def ble_cmd_ebr(self) -> str:
#         a = self._ble_cmd(ERROR_WHEN_BOOT_OR_RUN_CMD, 'SN')
#         if a and len(a.split()) == 2:
#             return a.split()[1].decode()[2:]
#         return 'error'
#
#     def ble_cmd_tst(self) -> bool:
#         a = self._ble_cmd(TEST_CMD)
#         return a == b'TST 00'
#
#     def ble_cmd_mts(self) -> bool:
#         a = self._ble_cmd(MY_TOOL_SET_CMD, 'SN')
#         return a == b'MTS 00'
#
#     def ble_cmd_frm(self) -> bool:
#         a = self._ble_cmd(FORMAT_CMD)
#         time.sleep(1)
#         return a == b'FRM 00'
#
#     def ble_cmd_dir_ext(self, ext) -> dict:  # pragma: no cover
#         # todo > check why sometimes no \x04
#         f_l = self._ble_cmd(DIR_CMD)
#         # removes DIR bad trailing sometimes
#         self.per.waitForNotifications(.1)
#         return lowell_file_list_as_dict(f_l, ext, match=True)
#
#     def ble_cmd_dir(self) -> dict:  # pragma: no cover
#         rv = self.ble_cmd_dir_ext('*')
#         return rv
#
#     def ble_cmd_del(self, file_name: str) -> bool:
#         a = self._ble_cmd(DEL_FILE_CMD, file_name)
#         return a == b'DEL 00'
#
#     def ble_cmd_crc(self, file_name: str) -> str:
#         a = self._ble_cmd(CRC_CMD, file_name)
#         if a and len(a.split()) == 2:
#             return a.split()[1].decode()[2:]
#         return 'error'
#
#     def ble_cmd_wli(self, info) -> str:
#         # info: 'SN1234567
#         valid = ['SN', 'BA', 'CA', 'MA']
#         assert info[:2] in valid
#         a = self._ble_cmd(LOGGER_INFO_CMD_W, info)
#         return 'ok' if a == b'WLI 00' else 'error'
#
#     def ble_cmd_rli(self) -> dict:
#         info = {}
#         a = self._ble_cmd(LOGGER_INFO_CMD, 'SN')
#         if a and len(a.split()) == 2:
#             info['SN'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(LOGGER_INFO_CMD, 'MA')
#         if a and len(a.split()) == 2:
#             info['MA'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(LOGGER_INFO_CMD, 'BA')
#         if a and len(a.split()) == 2:
#             info['BA'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(LOGGER_INFO_CMD, 'CA')
#         if a and len(a.split()) == 2:
#             info['CA'] = a.split()[1].decode()[2:]
#         return info
#
#     def ble_cmd_whs(self, data) -> bool:
#         valid = ['TMO', 'TMR', 'TMA', 'TMB', 'TMC']
#         assert data[:3] in valid
#         a = self._ble_cmd(LOGGER_HSA_CMD_W, 'TMO12345')
#         return a == b'WHS 00'
#
#     def ble_cmd_rhs(self) -> dict:
#         hsa = {}
#         a = self._ble_cmd(CALIBRATION_CMD, 'TMO')
#         if a and len(a.split()) == 2:
#             hsa['TMO'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(CALIBRATION_CMD, 'TMR')
#         if a and len(a.split()) == 2:
#             hsa['TMR'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(CALIBRATION_CMD, 'TMA')
#         if a and len(a.split()) == 2:
#             hsa['TMA'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(CALIBRATION_CMD, 'TMB')
#         if a and len(a.split()) == 2:
#             hsa['TMB'] = a.split()[1].decode()[2:]
#         a = self._ble_cmd(CALIBRATION_CMD, 'TMC')
#         if a and len(a.split()) == 2:
#             hsa['TMC'] = a.split()[1].decode()[2:]
#         return hsa
#
#     def ble_cmd_siz(self, file_name) -> int:
#         a = self._ble_cmd(SIZ_CMD, file_name)
#         if a and len(a.split()) == 2:
#             i = int(a.split()[1].decode()[2:])
#             return i
#         return 0
#
#     def ble_cmd_rst(self) -> bool:
#         a = self._ble_cmd(RESET_CMD)
#         return a == b'RST 00'
#
#     def ble_cmd_cfg(self, cfg_d) -> bool:
#         assert type(cfg_d) is dict
#         s = json.dumps(cfg_d)
#         a = self._ble_cmd(CONFIG_CMD, s)
#         return a == b'CFG 00'
#
#     def ble_cmd_run(self) -> bool:
#         a = self._ble_cmd(RUN_CMD)
#         return a == b'RUN 00'
#
#     def ble_cmd_rws(self, s) -> bool:
#         a = self._ble_cmd(RWS_CMD, s)
#         return a == b'RWS 00'
#
#     def ble_cmd_stp(self) -> bool:
#         a = self._ble_cmd(STOP_CMD)
#         v = (b'STP 00', b'STP 0200')
#         return a in v
#
#     def ble_cmd_sws(self, s) -> bool:
#         a = self._ble_cmd(SWS_CMD, s)
#         return a == b'SWS 00'
#
#     def ble_cmd_rfn(self) -> str:
#         a = self._ble_cmd(REQ_FILE_NAME_CMD)
#         if a == b'RFN 00':
#             return ''
#         if a and len(a.split()) == 2:
#             return a.split()[1].decode()[2:]
#         return 'error'
#
#     def _dwl_chunk(self, chunk_number) -> tuple:
#         # send DWL command
#         c_n = chunk_number
#         cmd = 'DWL {:02x}{}\r'.format(len(str(c_n)), c_n)
#         self._ble_write(cmd.encode())
#
#         # receive DWL answer
#         timeout = False
#         data = bytes()
#         last = time.perf_counter()
#         while 1:
#             # keep accumulating BLE notifications
#             if self.per.waitForNotifications(.1):
#                 last = time.perf_counter()
#
#             # timeout == last fragment (good) or error (bad)
#             if time.perf_counter() > last + 2:
#                 data += self.dlg.buf
#                 timeout = True
#                 break
#
#             # got 1 entire chunk, use >= because of race conditions
#             if len(self.dlg.buf) >= 2048:
#                 data += self.dlg.buf[:2048]
#                 self.dlg.buf = self.dlg.buf[2048:]
#                 break
#
#         return timeout, data
#
#     def ble_cmd_dwl(self, file_size, p=None) -> bytes:
#         # do not remove this, in case buffer has 'DWG 00'
#         self.dlg.buf = bytes()
#         data_file = bytes()
#         number_of_chunks = math.ceil(file_size / 2048)
#
#         # file-system based progress indicator
#         if p:
#             f = open(p, 'w+')
#             f.write(str(0))
#             f.close()
#
#         # download and update file w/ progress
#         for i in range(number_of_chunks):
#             timeout, data_chunk = self._dwl_chunk(i)
#             data_file += data_chunk
#             if p:
#                 f = open(p, 'w+')
#                 _ = len(data_file) / file_size * 100
#                 _ = _ if _ < 100 else 100
#                 f.write(str(_))
#                 f.close()
#
#         # truncate and return
#         self.dlg.buf = bytes()
#         if len(data_file) < file_size:
#             return bytes()
#         data_file = data_file[:file_size]
#         return data_file
#
#     def ble_cmd_dwg(self, name) -> bool:  # pragma: no cover
#         """ see if a file can be DWG-ed """
#
#         self.dlg.buf = bytes()
#         _ = '{} {:02x}{}\r'
#         cmd = _.format(DWG_FILE_CMD, len(name), name)
#         self._ble_write(cmd.encode())
#         self.per.waitForNotifications(5)
#         return self.dlg.buf == b'DWG 00'
#
#     def ble_cmd_mbl_ensure(self, v: str) -> bool:
#         assert v in '012'
#         for i in range(3):
#             rv = self.ble_cmd_mbl()
#             if v in '12' and v in ('on_1', 'on_2'):
#                 return True
#             if v == '0' and rv == 'off':
#                 return True
#         return False
#
#     def ble_cmd_wak_ensure(self, v: str) -> bool:
#         assert v.lower() in ('on', 'off')
#         rv = self.ble_cmd_wak()
#         if rv == v:
#             return True
#         rv = self.ble_cmd_wak()
#         if rv == v:
#             return True
#         return False
#


if __name__ == '__main__':
    mac = '11:22:33:44:55:66'
    lc = CC26X2RFake(mac)
    lc.open()
    # rv = lc.ble_cmd_sts()
    # rv = lc.ble_cmd_gtm()
    # rv = lc.ble_cmd_gfv()
    rv = lc.ble_cmd_bat()
    # rv = lc.ble_cmd_utm()

    print(rv)