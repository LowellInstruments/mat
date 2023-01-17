import asyncio
import json
import platform
from datetime import datetime, timezone, timedelta
import math
import time
import humanize
from bleak import BleakError, BleakClient
from mat.ble.ble_mat_utils import ble_mat_lowell_build_cmd as build_cmd, ble_mat_progress_dl, ble_mat_bluetoothctl_disconnect, \
    ble_mat_hci_exists
from mat.ble.bleak.cc26x2r_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD, STATUS_CMD, LOGGER_INFO_CMD_W, \
    LOGGER_INFO_CMD
from mat.logger_controller_ble import DWG_FILE_CMD, CRC_CMD, CONFIG_CMD, WAKE_CMD, OXYGEN_SENSOR_CMD, BAT_CMD, \
    FILE_EXISTS_CMD, WAT_CMD
from mat.utils import lowell_cmd_dir_ans_to_dict


GPS_FRM_STR = '{:+.6f}'


class BleCC26X2Sim:
    def __init__(self, h='hci0', dbg_ans=False):
        self.is_connected = False
        self.mac = ''
        self.files = {'MAT.cfg': 189}
        self.gps_string = ''

    async def connect(self, mac):
        self.mac = None
        if mac.startswith('11:22:33'):
            self.mac = mac
            return 0
        return 1

    async def disconnect(self):
        self.mac = ''

    @staticmethod
    async def cmd_stm():
        return 0

    async def cmd_dwg(self, s):
        return 0 if s in self.files.keys() else 1

#     async def cmd_crc(self, s):
#         c, _ = build_cmd(CRC_CMD, s)
#         await self._cmd(c)
#         rv = await self._ans_wait()
#         ok = rv and len(rv) == 14 and rv.startswith(b'CRC')
#         if ok:
#             return 0, rv[-8:].decode().lower()
#         return 1, ''
#
    async def cmd_del(self, s):
        try:
            del self.files[s]
            return 0
        except (Exception, ):
            return 1

    async def cmd_fex(self, s):
        # todo > check if this exists on firmware
        return 0 if s in self.files.keys() else 1

    @staticmethod
    async def cmd_gtm():
        dt = datetime.now(timezone.utc)
        s_dt = dt.strftime('%Y/%m/%d %H:%M:%S')
        return 0, s_dt

    @staticmethod
    async def cmd_stp():
        return 0

    @staticmethod
    async def cmd_led():
        return 0

    async def cmd_frm(self):
        self.files = {}
        return 0

    async def cmd_sws(self, g):
        self.gps_string = g
        return 0

    async def cmd_rws(self, g):
        self.gps_string = g
        return 0

    async def cmd_mts(self):
        self.files['mts_file'] = 1245
        return 0

    async def cmd_dir(self) -> tuple:
        a = ''
        for k, v in self.files.items():
            a += '\n\r{}\t\t\t{}\n\r'.format(k, v)
        a += '\4\n\r'
        ls = lowell_cmd_dir_ans_to_dict(a.encode(), '*', match=True)
        return 0, ls

    async def cmd_cfg(self, cfg_d):
        assert type(cfg_d) is dict
        self.files['MAT.cfg'] = 189
        return 0

    @staticmethod
    async def cmd_wli(s):
        return 0

#     async def cmd_gdo(self):
#         c, _ = build_cmd(OXYGEN_SENSOR_CMD)
#         await self._cmd(c)
#         rv = await self._ans_wait()
#         ok = rv and len(rv) == 18 and rv.startswith(b'GDO')
#         if not ok:
#             return
#         a = rv
#         if a and len(a.split()) == 2:
#             # a: b'GDO 0c112233445566'
#             _ = a.split()[1].decode()
#             dos, dop, dot = _[2:6], _[6:10], _[10:14]
#             dos = dos[-2:] + dos[:2]
#             dop = dop[-2:] + dop[:2]
#             dot = dot[-2:] + dot[:2]
#             if dos.isnumeric():
#                 return dos, dop, dot

    @staticmethod
    async def cmd_bat():
        return 0, 2456

#     async def cmd_wat(self):
#         c, _ = build_cmd(WAT_CMD)
#         await self._cmd(c)
#         rv = await self._ans_wait()
#         print(rv)
#         ok = rv and len(rv) == 10 and rv.startswith(b'WAT')
#         print(rv)
#         if not ok:
#             return
#         a = rv
#         if a and len(a.split()) == 2:
#             _ = a.split()[1].decode()
#             w = _[-2:] + _[-4:-2]
#             w = int(w, 16)
#             return 0, w
#         return 1, 0
#
#     async def cmd_wak(self, s):
#         assert s in ('on', 'off')
#         c, _ = build_cmd(WAKE_CMD)
#         await self._cmd(c)
#         rv = await self._ans_wait()
#         if s == 'off' and rv == b'WAK 0200':
#             return 0
#         if s == 'on' and rv == b'WAK 0201':
#             return 0
#         return 1
#
#     async def cmd_rli(self):
#         info = {}
#         for each in ['SN', 'BA', 'CA', 'MA']:
#             c, _ = build_cmd(LOGGER_INFO_CMD, each)
#             await self._cmd(c)
#             rv = await self._ans_wait()
#             if rv and len(rv.split()) == 2:
#                 info[each] = rv.split()[1].decode()[2:]
#         return 0 if len(info) == 4 else 1
#
#     async def cmd_sts(self):
#         await self._cmd('STS \r')
#         rv = await self._ans_wait()
#         ok = rv and len(rv) == 8 and rv.startswith(b'STS')
#         if ok:
#             _ = {
#                 b'0200': 'running',
#                 b'0201': 'stopped',
#                 b'0203': 'delayed',
#                 # depending on version 'delayed' has 2
#                 b'0202': 'delayed',
#             }
#             state = _[rv.split(b' ')[1]]
#         return 0, state if ok else 1, 'error'

    @staticmethod
    async def cmd_run():
        return 0

    @staticmethod
    async def cmd_gfv():
        return 0, '4.4.44'

#     async def cmd_dwl(self, z, ip=None, port=None) -> tuple:
#
#         # z: file size
#         self.ans = bytes()
#         n = math.ceil(z / 2048)
#         ble_mat_progress_dl(0, z, ip, port)
#
#         for i in range(n):
#             c = 'DWL {:02x}{}\r'.format(len(str(i)), i)
#             await self._cmd(c, empty=False)
#             for _ in range(20):
#                 await self._ans_wait(timeout=.2)
#                 if len(self.ans) == (i + 1) * 2048:
#                     break
#                 if len(self.ans) == z:
#                     break
#             ble_mat_progress_dl(len(self.ans), z, ip, port)
#             # print('chunk #{} len {}'.format(i, len(self.ans)))
#
#         rv = 0 if z == len(self.ans) else 1
#         return rv, self.ans

    async def cmd_utm(self):
        return 0, '3 days'
