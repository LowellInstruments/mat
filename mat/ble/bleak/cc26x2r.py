import asyncio
import json
from datetime import datetime, timezone, timedelta
import math
import time
import humanize
from bleak import BleakError, BleakClient
from mat.ble.ble_utils import ble_lowell_build_cmd as build_cmd, ble_progress_dl, sh_bluetoothctl_disconnect, \
    sh_hci_exists
from mat.ble.bleak.cc26x2r_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD, STATUS_CMD, LOGGER_INFO_CMD_W, \
    LOGGER_INFO_CMD
from mat.logger_controller_ble import DWG_FILE_CMD, CRC_CMD, CONFIG_CMD, WAKE_CMD, OXYGEN_SENSOR_CMD, BAT_CMD
from mat.utils import dir_ans_to_dict


UUID_T = 'f0001132-0451-4000-b000-000000000000'
UUID_R = 'f0001131-0451-4000-b000-000000000000'


class BleCC26X2:
    def __init__(self, h='hci0'):
        self.cli = None
        self.ans = bytes()
        self.tag = ''
        # _cd: _command_done
        assert h.startswith('hci')
        sh_hci_exists(h)
        self.h = h
        sh_bluetoothctl_disconnect()

    async def _cmd(self, c: str, empty=True):
        self.tag = c[:3]
        if empty:
            self.ans = bytes()
        print('<', c)
        await self.cli.write_gatt_char(UUID_R, c.encode())

    async def _ans_wait(self, timeout=1.0):
        is_dwl = self.tag == 'DWL'

        while self.cli and self.cli.is_connected:

            # accumulate in notification handler
            await asyncio.sleep(0.1)
            timeout -= 0.1

            # see if no more to receive
            if is_cmd_done(self.tag, self.ans):
                print('>', self.ans)
                return self.ans

            # evaluate here, not in loop condition
            if timeout <= 0:
                break

        # print summary of executed command
        if is_dwl:
            return self.ans

        print('[ BLE ] timeout -> cmd {}'.format(self.tag))

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
        rv = await self._ans_wait(timeout=5)
        return 0 if rv == b'DWG 00' else 1

    async def cmd_crc(self, s):
        c, _ = build_cmd(CRC_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=10)
        ok = len(rv) == 14 and rv.startswith(b'CRC')
        if ok:
            return 0, rv[-8:].decode().lower()
        return 1, 'crc_error'

    async def cmd_del(self, s):
        c, _ = build_cmd(DEL_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=10)
        return 0 if rv == b'DEL 00' else 1

    async def cmd_gtm(self):
        await self._cmd('GTM \r')
        rv = await self._ans_wait()
        ok = len(rv) == 25 and rv.startswith(b'GTM')
        return 0 if ok else 1

    async def cmd_stp(self):
        await self._cmd('STP \r')
        rv = await self._ans_wait()
        ok = rv in (b'STP 00', b'STP 0200')
        return 0 if ok else 1

    async def cmd_led(self):
        await self._cmd('LED \r')
        rv = await self._ans_wait(timeout=3)
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
        rv = await self._ans_wait(timeout=4)
        ok = len(rv) == 18 and rv.startswith(b'GDO')
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
        ok = len(rv) == 10 and rv.startswith(b'BAT')
        if not ok:
            return
        a = rv
        if a and len(a.split()) == 2:
            # a: b'BAT 04BD08'
            _ = a.split()[1].decode()
            b = _[-2:] + _[-4:-2]
            b = int(b, 16)
            print('bat is {} mV'.format(b))
            return b

    async def cmd_wak(self, s):
        assert s in ('on', 'off')
        c, _ = build_cmd(WAKE_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        if s == 'off' and rv == b'WAK 0200':
            return 0
        if s == 'on' and rv == b'WAK 0201':
            return 0
        return 1

    async def cmd_rli(self):
        info = {}
        for each in ['SN', 'BA', 'CA', 'MA']:
            c, _ = build_cmd(LOGGER_INFO_CMD, each)
            await self._cmd(c)
            rv = await self._ans_wait()
            if rv and len(rv.split()) == 2:
                info[each] = rv.split()[1].decode()[2:]
        return 0 if len(info) == 4 else 1

    async def cmd_sts(self):
        await self._cmd('STS \r')
        rv = await self._ans_wait()
        ok = len(rv) == 8 and rv.startswith(b'STS')
        return 0 if ok else 1

    async def cmd_run(self):
        await self._cmd('RUN \r')
        rv = await self._ans_wait()
        ok = rv in (b'RUN 00', b'RUN 0200')
        return 0 if ok else 1

    async def cmd_mts(self):
        await self._cmd('MTS \r')
        rv = await self._ans_wait(timeout=20)
        return 0 if rv == b'MTS 00' else 1

    async def cmd_sws(self, g):
        # STOP with STRING
        lat, lon, _, __ = g
        lat = '{:+.6f}'.format(float(lat))
        lon = '{:+.6f}'.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(SWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=3)
        print(rv)
        ok = rv in (b'SWS 00', b'SWS 0200')
        return 0 if ok else 1

    async def cmd_rws(self, g):
        # RUN with STRING
        lat, lon, _, __ = g
        lat = '{:+.6f}'.format(float(lat))
        lon = '{:+.6f}'.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(RWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv in (b'RWS 00', b'RWS 0200')
        return 0 if ok else 1

    async def cmd_gfv(self):
        await self._cmd('GFV \r')
        rv = await self._ans_wait()
        ok = len(rv) == 12 and rv.startswith(b'GFV')
        return 0 if ok else 1

    async def cmd_dir(self) -> tuple:
        await self._cmd('DIR \r')
        rv = await self._ans_wait(timeout=3.0)
        if not rv:
            return 1, 'not'
        if rv == b'ERR':
            return 2, 'error'
        if rv and not rv.endswith(b'\x04\n\r'):
            return 3, 'partial'
        ls = dir_ans_to_dict(rv, '*', match=True)
        return 0, ls

    async def cmd_dwl(self, z, ip=None, port=None) -> tuple:

        # z: file size
        self.ans = bytes()
        n = math.ceil(z / 2048)
        ble_progress_dl(0, z, ip, port)

        for i in range(n):
            c = 'DWL {:02x}{}\r'.format(len(str(i)), i)
            await self._cmd(c, empty=False)
            for j in range(20):
                await self._ans_wait(timeout=.2)
                if len(self.ans) == (i + 1) * 2048:
                    break
                if len(self.ans) == z:
                    break
            ble_progress_dl(len(self.ans), z, ip, port)
            # print('chunk #{} len {}'.format(i, len(self.ans)))

        rv = 0 if z == len(self.ans) else 1
        return rv, self.ans

    async def disconnect(self):
        if self.cli and self.cli.is_connected:
            await self.cli.disconnect()

    async def connect(self, mac):
        def cb_disc(_: BleakClient):
            pass

        def c_rx(_: int, b: bytearray):
            self.ans += b

        for i in range(3):
            try:
                # we pass hci here
                h = self.h
                self.cli = BleakClient(mac, adapter=h, disconnected_callback=cb_disc)
                if await self.cli.connect():
                    await self.cli.start_notify(UUID_T, c_rx)
                    return 0
            except (asyncio.TimeoutError, BleakError, OSError):
                print('connection attempt {} of 3 failed'.format(i + 1))
                time.sleep(1)
        return 1

    async def cmd_utm(self):
        await self._cmd('UTM \r')
        rv = await self._ans_wait()
        ok = len(rv) == 14 and rv.startswith(b'UTM')
        if ok:
            _ = self.ans.split()[1].decode()
            b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
            t = int(b, 16)
            s = humanize.naturaldelta(timedelta(seconds=t))
            print('utm', s)
            return 0, s
        return 1, ''
