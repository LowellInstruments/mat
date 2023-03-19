import os
import asyncio
import json
import platform
import pytest
from datetime import datetime, timezone, timedelta
import math
import time
import humanize
from bleak import BleakError, BleakClient, BleakScanner
from mat.ble.ble_mat_utils import ble_mat_lowell_build_cmd as build_cmd, ble_mat_progress_dl, \
    ble_mat_bluetoothctl_disconnect, \
    ble_mat_hci_exists, ble_rfkill_wlan
from mat.ble.bleak.cc26x2r_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD, STATUS_CMD, LOGGER_INFO_CMD_W, \
    LOGGER_INFO_CMD
from mat.logger_controller_ble import DWG_FILE_CMD, CRC_CMD, CONFIG_CMD, WAKE_CMD, OXYGEN_SENSOR_CMD, BAT_CMD, \
    FILE_EXISTS_CMD, WAT_CMD, LOG_EN_CMD, PRF_TIME_CMD, PRF_TIME_CMD_GET, PRF_TIME_EN
from mat.utils import lowell_cmd_dir_ans_to_dict, linux_is_rpi


UUID_T = 'f0001132-0451-4000-b000-000000000000'
UUID_R = 'f0001131-0451-4000-b000-000000000000'
GPS_FRM_STR = '{:+.6f}'


class BleCC26X2:
    def __init__(self, h='hci0', dbg_ans=False):
        self.cli = None
        self.ans = bytes()
        self.tag = ''
        self.dbg_ans = dbg_ans
        if platform.system() == 'Linux':
            assert h.startswith('hci')
            ble_mat_hci_exists(h)
        self.h = h
        # nice trick to start with fresh page
        ble_mat_bluetoothctl_disconnect()

    async def is_connected(self):
        return self.cli and self.cli.is_connected

    async def _cmd(self, c: str, empty=True):
        self.tag = c[:3]
        if empty:
            self.ans = bytes()

        if self.dbg_ans:
            print('<', c)

        await self.cli.write_gatt_char(UUID_R, c.encode())

    async def _ans_wait(self, timeout=10.0):

        # for benchmark purposes
        start = time.time()

        # accumulate command answer in notification handler
        while self.cli and self.cli.is_connected and timeout > 0:
            await asyncio.sleep(0.1)
            timeout -= 0.1

            # ---------------------------------
            # considers the command answered
            # ---------------------------------

            if is_cmd_done(self.tag, self.ans):
                if self.dbg_ans:
                    # debug good answers
                    elapsed = time.time() - start
                    print('>', self.ans)
                    print('\ttook {} secs'.format(int(elapsed)))
                return self.ans

        # DWL is sort of special command
        if self.tag == 'DWL':
            return self.ans

        # allows debugging timeouts
        elapsed = int(time.time() - start)

        # useful in case we have errors
        print('[ BLE ] timeout {} for cmd {}'.format(elapsed, self.tag))
        if not self.ans:
            return
        print('\t dbg_ans:', self.ans)

        # detect extra errors :)
        n = int(len(self.ans) / 2)
        if self.ans[:n] == self.ans[n:]:
            e = 'error duplicate answer: {} \n' \
                'seems you used PWA recently \n' \
                'and Linux BLE stack got crazy, \n' \
                'just run $ systemctl restart bluetooth'
            print(e.format(self.ans))

    async def cmd_stm(self):
        # time() -> seconds since epoch, in UTC
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        c, _ = build_cmd(SET_TIME_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'STM 00' else 1

    async def cmd_dwg(self, s):
        c, _ = build_cmd(DWG_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'DWG 00' else 1

    async def cmd_crc(self, s):
        c, _ = build_cmd(CRC_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and len(rv) == 14 and rv.startswith(b'CRC')
        if ok:
            return 0, rv[-8:].decode().lower()
        return 1, ''

    async def cmd_del(self, s):
        c, _ = build_cmd(DEL_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        return 0 if rv == b'DEL 00' else 1

    async def cmd_fex(self, s):
        c, _ = build_cmd(FILE_EXISTS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        # return 0 == OK if file exists
        return 0 if rv == b'FEX 01' else 1

    async def cmd_gtm(self):
        await self._cmd('GTM \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 25 and rv.startswith(b'GTM')
        if not ok:
            return 1, ''
        return 0, rv[6:].decode()

    async def cmd_stp(self):
        await self._cmd('STP \r')
        rv = await self._ans_wait(timeout=30)
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

    async def cmd_wli(self, s):
        c, _ = build_cmd(LOGGER_INFO_CMD_W, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv == b'WLI 00'
        return 0 if ok else 1

    async def cmd_gdo(self):
        c, _ = build_cmd(OXYGEN_SENSOR_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and len(rv) == 18 and rv.startswith(b'GDO')
        if not ok:
            return
        a = rv
        if a and len(a.split()) == 2:
            # a: b'GDO 0c112233445566'
            _ = a.split()[1].decode()
            dos, dop, dot = _[2:6], _[6:10], _[10:14]
            dos = dos[-2:] + dos[:2]
            dop = dop[-2:] + dop[:2]
            dot = dot[-2:] + dot[:2]
            if dos.isnumeric():
                return dos, dop, dot

    async def cmd_bat(self):
        c, _ = build_cmd(BAT_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and len(rv) == 10 and rv.startswith(b'BAT')
        if not ok:
            return
        a = rv
        if a and len(a.split()) == 2:
            # a: b'BAT 04BD08'
            _ = a.split()[1].decode()
            b = _[-2:] + _[-4:-2]
            b = int(b, 16)
            return 0, b
        return 1, 0

    async def cmd_wat(self):
        c, _ = build_cmd(WAT_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        print(rv)
        ok = rv and len(rv) == 10 and rv.startswith(b'WAT')
        print(rv)
        if not ok:
            return
        a = rv
        if a and len(a.split()) == 2:
            _ = a.split()[1].decode()
            w = _[-2:] + _[-4:-2]
            w = int(w, 16)
            return 0, w
        return 1, 0

    async def cmd_wak(self, s):
        assert s in ('on', 'off')
        c, _ = build_cmd(WAKE_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        if s == 'off' and rv == b'WAK 0200':
            return 0
        if s == 'on' and rv == b'WAK 0201':
            return 0
        # just toggle again :)
        await asyncio.sleep(.1)
        await self._cmd(c)
        rv = await self._ans_wait()
        if s == 'off' and rv == b'WAK 0200':
            return 0
        if s == 'on' and rv == b'WAK 0201':
            return 0
        return 1

    async def cmd_log(self):
        c, _ = build_cmd(LOG_EN_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'LOG 0201':
            return 0, 1
        if rv == b'LOG 0200':
            return 0, 0
        return 1, 0

    async def cmd_bla(self):
        c, _ = build_cmd('BLA')
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'BLA 0201':
            return 0, 1
        if rv == b'BLA 0200':
            return 0, 0
        return 1, 0

    async def cmd_pfe(self):
        c, _ = build_cmd(PRF_TIME_EN)
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'PFE 0201':
            return 0, 1
        if rv == b'PFE 0200':
            return 0, 0
        return 1, 0

    async def cmd_pft(self):
        c, _ = build_cmd(PRF_TIME_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'PFT 0200':
            return 0, 0
        if rv == b'PFT 0201':
            return 0, 1
        if rv == b'PFT 0202':
            return 0, 2
        if rv == b'PFT 0203':
            return 0, 3
        return 1, 0

    async def cmd_pfg(self):
        c, _ = build_cmd(PRF_TIME_CMD_GET)
        await self._cmd(c)
        rv = await self._ans_wait()
        print(rv)
        if rv == b'PFG 0200':
            return 0, 0
        if rv == b'PFG 0201':
            return 0, 1
        if rv == b'PFG 0202':
            return 0, 2
        if rv == b'PFG 0203':
            return 0, 3
        return 1, 0

    async def cmd_rli(self):
        info = {}
        all_ok = True
        for each in ['SN', 'BA', 'CA', 'MA']:
            c, _ = build_cmd(LOGGER_INFO_CMD, each)
            await self._cmd(c)
            rv = await self._ans_wait()
            if not rv or rv == b'ERR':
                all_ok = False
            else:
                info[each] = rv.decode()[6:]
            await asyncio.sleep(.1)
        if all_ok:
            return 0, info
        return 1, info

    async def cmd_sts(self):
        await self._cmd('STS \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 8 and rv.startswith(b'STS')
        if ok:
            _ = {
                b'0200': 'running',
                b'0201': 'stopped',
                b'0203': 'delayed',
                # depending on version 'delayed' has 2
                b'0202': 'delayed',
            }
            state = _[rv.split(b' ')[1]]
        if ok:
            return 0, state
        return 1, 'error'

    async def cmd_run(self):
        await self._cmd('RUN \r')
        rv = await self._ans_wait(timeout=30)
        ok = rv in (b'RUN 00', b'RUN 0200')
        return 0 if ok else 1

    async def cmd_mts(self):
        await self._cmd('MTS \r')
        rv = await self._ans_wait(timeout=60)
        return 0 if rv == b'MTS 00' else 1

    async def cmd_sws(self, g):
        # STOP with STRING
        lat, lon, _, __ = g
        lat = GPS_FRM_STR.format(float(lat))
        lon = GPS_FRM_STR.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(SWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        ok = rv in (b'SWS 00', b'SWS 0200')
        return 0 if ok else 1

    async def cmd_rws(self, g):
        # RUN with STRING
        lat, lon, _, __ = g
        lat = GPS_FRM_STR.format(float(lat))
        lon = GPS_FRM_STR.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(RWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        ok = rv in (b'RWS 00', b'RWS 0200')
        return 0 if ok else 1

    async def cmd_gfv(self):
        await self._cmd('GFV \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 12 and rv.startswith(b'GFV')
        if not ok:
            return 1, ''
        return 0, rv[6:].decode()

    async def cmd_dir(self) -> tuple:
        await self._cmd('DIR \r')
        rv = await self._ans_wait(timeout=30)
        if not rv:
            return 1, 'not'
        if rv == b'ERR':
            return 2, 'error'
        if rv and not rv.endswith(b'\x04\n\r'):
            return 3, 'partial'
        ls = lowell_cmd_dir_ans_to_dict(rv, '*', match=True)
        return 0, ls

    async def cmd_dwl(self, z, ip=None, port=None) -> tuple:

        # z: file size
        self.ans = bytes()
        n = math.ceil(z / 2048)
        ble_mat_progress_dl(0, z, ip, port)

        for i in range(n):
            c = 'DWL {:02x}{}\r'.format(len(str(i)), i)
            await self._cmd(c, empty=False)
            for _ in range(20):
                await self._ans_wait(timeout=.2)
                if len(self.ans) == (i + 1) * 2048:
                    break
                if len(self.ans) == z:
                    break
            ble_mat_progress_dl(len(self.ans), z, ip, port)
            # print('chunk #{} len {}'.format(i, len(self.ans)))

        rv = 0 if z == len(self.ans) else 1
        return rv, self.ans

    async def disconnect(self):
        try:
            await self.cli.disconnect()
        except (Exception, ):
            pass

    # --------------------
    # connection routine
    # --------------------

    async def _connect_rpi(self, mac, rfk=False):
        def c_rx(_: int, b: bytearray):
            self.ans += b

        till = time.perf_counter() + 30
        h = self.h
        self.cli = BleakClient(mac, adapter=h)
        rv: int

        while True:
            now = time.perf_counter()
            if now > till:
                print('_connect_rpi totally failed')
                rv = 1
                break

            try:
                if await self.cli.connect():
                    await self.cli.start_notify(UUID_T, c_rx)
                    rv = 0
                    break

            except (asyncio.TimeoutError, BleakError, OSError) as ex:
                _ = int(till - time.perf_counter())
                print('_connect_rpi failed, {} seconds left'.format(_))
                print(ex)
                await asyncio.sleep(.5)

        return rv

    async def _connect(self, mac):
        def c_rx(_: int, b: bytearray):
            self.ans += b

        n = 3
        for i in range(n):
            try:
                # we pass hci here
                h = self.h
                self.cli = BleakClient(mac, adapter=h)
                if await self.cli.connect(timeout=10):
                    await self.cli.start_notify(UUID_T, c_rx)
                    return 0

            except (asyncio.TimeoutError, BleakError, OSError) as ex:
                e = 'connect attempt {} of {} failed, h {}'
                print(e.format(i + 1, n, self.h))
                print(ex)
                await asyncio.sleep(1)
                # time.sleep(.1)
        return 1

    async def connect(self, mac, rfk=False):
        if linux_is_rpi():
            if rfk:
                await ble_rfkill_wlan('block')
            rv = await self._connect_rpi(mac, rfk)
            if rfk:
                await ble_rfkill_wlan('unblock')
            return rv

        # when not Raspberry
        return await self._connect(mac)

    async def cmd_utm(self):
        await self._cmd('UTM \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 14 and rv.startswith(b'UTM')
        if ok:
            _ = self.ans.split()[1].decode()
            b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
            t = int(b, 16)
            s = humanize.naturaldelta(timedelta(seconds=t))
            return 0, s
        return 1, ''
