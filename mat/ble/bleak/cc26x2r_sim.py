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
    LOGGER_INFO_CMD, STOP_CMD, DIR_CMD, TIME_CMD
from mat.logger_controller_ble import DWG_FILE_CMD, CRC_CMD, CONFIG_CMD, WAKE_CMD, OXYGEN_SENSOR_CMD, BAT_CMD, \
    FILE_EXISTS_CMD, WAT_CMD, FORMAT_CMD, LED_CMD, MY_TOOL_SET_CMD
from mat.utils import lowell_cmd_dir_ans_to_dict


GPS_FRM_STR = '{:+.6f}'


class BleCC26X2Sim:
    def __init__(self):
        self.tag = bytes()
        self.cmd = bytes()
        self.files = {
            'MAT.cfg': 189,
        }
        self.connected = False

    async def disconnect(self):
        self.connected = False
        return 0

    async def connect(self, mac):
        self.connected = mac.startswith('11:22:33')
        return 0 if self.connected else 1

    async def is_connected(self):
        return self.connected

    async def _cmd(self, c: str):
        self.tag = c[:3]
        return await self._ans_wait(timeout=.1)

    async def _ans_wait(self, timeout=.1):

        # ---------------------------------------
        # this function simulates FIRMWARE
        # ---------------------------------------

        a = bytes()
        t = self.tag
        await asyncio.sleep(timeout)

        if t == STATUS_CMD:
            a = b'STS 0201'
        elif t == SET_TIME_CMD:
            a = b'STM 00'
        elif t == STOP_CMD:
            a = b'STP 00'
        elif t == FORMAT_CMD:
            a = b'FRM 00'
        elif t == TIME_CMD:
            dt = datetime.now()
            s_dt = dt.strftime('%Y/%m/%d %H:%M:%S')
            a = 'GTM 19{}'.format(s_dt).encode()
        elif t == SWS_CMD:
            a = b'SWS 00'
        elif t == RWS_CMD:
            a = b'RWS 00'
        elif t == LED_CMD:
            a = b'LED 00'
        elif t == MY_TOOL_SET_CMD:
            i = time.time()
            s = 'file_{}.lid'.format(i)
            self.files[s] = i
            a = b'MTS 00'
        elif t == CONFIG_CMD:
            none_present = 'MAT.cfg' not in self.files.keys()
            a = b'CFG 00' if none_present else None
        elif t == DIR_CMD:
            for k, v in self.files.items():
                a += '\n\r{}\t\t\t{}\n\r'.format(k, v).encode()
            a += b'\4\n\r'
        else:
            assert 'wtf command'
        return a

    async def cmd_sts(self):
        rv = await self._cmd(STATUS_CMD)
        is_in_states = rv in (
            b'STS 0200',
            b'STS 0201',
            b'STS 0202',
            b'STS 0203',
        )
        return 0 if is_in_states else 1

    async def cmd_stm(self):
        rv = await self._cmd(SET_TIME_CMD)
        return 0 if rv == b'STM 00' else 1

    async def cmd_dwg(self, s):
        return 0 if s in self.files.keys() else 1

    async def cmd_crc(self, s):
        if s not in self.files.keys():
            return 1, ''
        return 0, 'coffeeff'

    async def cmd_sws(self, g):
        # STOP with STRING
        lat, lon, _, __ = g
        lat = GPS_FRM_STR.format(float(lat))
        lon = GPS_FRM_STR.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(SWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv in (b'SWS 00', b'SWS 0200') else 1

    async def cmd_rws(self, g):
        # RUN with STRING
        lat, lon, _, __ = g
        lat = GPS_FRM_STR.format(float(lat))
        lon = GPS_FRM_STR.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(RWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv in (b'RWS 00', b'RWS 0200') else 1

    async def cmd_mts(self):
        await self._cmd('MTS \r')
        rv = await self._ans_wait()
        return 0 if rv == b'MTS 00' else 1

    async def cmd_del(self, s):
        try:
            del self.files[s]
            return 0
        except (Exception, ):
            return 1

    async def cmd_fex(self, s):
        return 0 if s in self.files.keys() else 1

    async def cmd_gtm(self):
        await self._cmd('GTM \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 25 and rv.startswith(b'GTM')
        if not ok:
            return 1, ''
        return 0, rv[6:].decode()

    async def cmd_stp(self):
        await self._cmd('STP \r')
        rv = await self._ans_wait()
        ok = rv in (b'STP 00', b'STP 0200')
        return 0 if ok else 1

    async def cmd_led(self):
        await self._cmd('LED \r')
        rv = await self._ans_wait()
        ok = rv == b'LED 00'
        return 0 if ok else 1

    async def cmd_frm(self):
        await self._cmd('FRM \r')
        rv = await self._ans_wait()
        self.files = {}
        ok = rv == b'FRM 00'
        return 0 if ok else 1

    async def cmd_cfg(self, cfg_d):
        assert type(cfg_d) is dict
        s = json.dumps(cfg_d)
        c, _ = build_cmd(CONFIG_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv == b'CFG 00'
        return 0 if ok else 1

    async def cmd_dir(self) -> tuple:
        await self._cmd('DIR \r')
        rv = await self._ans_wait()
        ls = lowell_cmd_dir_ans_to_dict(rv, '*', match=True)
        return 0, ls

    # async def cmd_gdo(self):
    #     c, _ = build_cmd(OXYGEN_SENSOR_CMD)
    #     await self._cmd(c)
    #     rv = await self._ans_wait()
    #     ok = rv and len(rv) == 18 and rv.startswith(b'GDO')
    #     if not ok:
    #         return
    #     a = rv
    #     if a and len(a.split()) == 2:
    #         # a: b'GDO 0c112233445566'
    #         _ = a.split()[1].decode()
    #         dos, dop, dot = _[2:6], _[6:10], _[10:14]
    #         dos = dos[-2:] + dos[:2]
    #         dop = dop[-2:] + dop[:2]
    #         dot = dot[-2:] + dot[:2]
    #         if dos.isnumeric():
    #             return dos, dop, dot
    #
    # async def cmd_bat(self):
    #     c, _ = build_cmd(BAT_CMD)
    #     await self._cmd(c)
    #     rv = await self._ans_wait()
    #     ok = rv and len(rv) == 10 and rv.startswith(b'BAT')
    #     if not ok:
    #         return
    #     a = rv
    #     if a and len(a.split()) == 2:
    #         # a: b'BAT 04BD08'
    #         _ = a.split()[1].decode()
    #         b = _[-2:] + _[-4:-2]
    #         b = int(b, 16)
    #         return 0, b
    #     return 1, 0
    #
    # async def cmd_wak(self, s):
    #     assert s in ('on', 'off')
    #     c, _ = build_cmd(WAKE_CMD)
    #     await self._cmd(c)
    #     rv = await self._ans_wait()
    #     if s == 'off' and rv == b'WAK 0200':
    #         return 0
    #     if s == 'on' and rv == b'WAK 0201':
    #         return 0
    #     return 1
    #
    # async def cmd_run(self):
    #     await self._cmd('RUN \r')
    #     rv = await self._ans_wait(timeout=30)
    #     ok = rv in (b'RUN 00', b'RUN 0200')
    #     return 0 if ok else 1
    #
    #
    # async def cmd_gfv(self):
    #     await self._cmd('GFV \r')
    #     rv = await self._ans_wait()
    #     ok = rv and len(rv) == 12 and rv.startswith(b'GFV')
    #     if not ok:
    #         return 1, ''
    #     return 0, rv[6:].decode()
    #
    # async def cmd_dwl(self, z, ip=None, port=None) -> tuple:
    #
    #     # z: file size
    #     self.ans = bytes()
    #     n = math.ceil(z / 2048)
    #     ble_mat_progress_dl(0, z, ip, port)
    #
    #     for i in range(n):
    #         c = 'DWL {:02x}{}\r'.format(len(str(i)), i)
    #         await self._cmd(c, empty=False)
    #         for _ in range(20):
    #             await self._ans_wait(timeout=.2)
    #             if len(self.ans) == (i + 1) * 2048:
    #                 break
    #             if len(self.ans) == z:
    #                 break
    #         ble_mat_progress_dl(len(self.ans), z, ip, port)
    #         # print('chunk #{} len {}'.format(i, len(self.ans)))
    #
    #     rv = 0 if z == len(self.ans) else 1
    #     return rv, self.ans
    #

    # async def cmd_utm(self):
    #     await self._cmd('UTM \r')
    #     rv = await self._ans_wait()
    #     ok = rv and len(rv) == 14 and rv.startswith(b'UTM')
    #     if ok:
    #         _ = self.ans.split()[1].decode()
    #         b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
    #         t = int(b, 16)
    #         s = humanize.naturaldelta(timedelta(seconds=t))
    #         return 0, s
    #     return 1, ''
