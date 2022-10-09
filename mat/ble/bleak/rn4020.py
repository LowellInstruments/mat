import asyncio
from datetime import datetime, timezone, timedelta
import time
from bleak import BleakError, BleakClient
from mat.ble.ble_utils import ble_lowell_build_cmd as build_cmd, ble_progress_dl, sh_bluetoothctl_reset
from mat.ble.bleak.rn4020_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD
from mat.utils import dir_ans_to_dict


UUID_T = UUID_R = '00035b03-58e6-07dd-021a-08123a000301'


class BleRN4020:
    def __init__(self, h='hci0'):
        self.cli = None
        self.ans = bytes()
        self.tag = ''
        # _cd: _command_done
        self._cd = False
        assert h.startswith('hci')
        self.h = h
        sh_bluetoothctl_reset()

    async def _cmd(self, c: str, empty=True):
        self._cd = False
        self.tag = c[:3]
        if empty:
            self.ans = bytes()
        print('<', c)
        # todo > fix this for RN4020 for STM for example
        await self.cli.write_gatt_char(UUID_R, c.encode())

    async def _ans_wait(self, timeout=1.0):
        while (not self._cd) and \
                (self.cli and self.cli.is_connected) and \
                (timeout > 0):

            # accumulate in notification handler
            await asyncio.sleep(0.1)
            timeout -= 0.1

            # see if no more to receive
            self._cd = is_cmd_done(self.tag, self.ans)
            if self._cd:
                break

        # print summary of executed command
        if self._cd:
            print('>', self.ans)
        else:
            print('[ BLE ] timeout -> cmd {}'.format(self.tag))
        return self.ans

    async def cmd_stm(self):
        # time() -> seconds since epoch, in UTC
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        c, _ = build_cmd(SET_TIME_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'\n\rSTM 00\r\n' else 1

    # async def cmd_del(self, s):
    #     c, _ = build_cmd(DEL_FILE_CMD, s)
    #     await self._cmd(c)
    #     rv = await self._ans_wait(timeout=10)
    #     return 0 if rv == b'DEL 00' else 1

    async def cmd_gtm(self):
        await self._cmd('GTM \r')
        rv = await self._ans_wait()
        ok = len(rv) == 29 and rv.startswith(b'\n\rGTM')
        return 0 if ok else 1

    async def cmd_stp(self):
        await self._cmd('STP \r')
        rv = await self._ans_wait()
        ok = len(rv) == 12 and rv.startswith(b'\n\rSTP')
        return 0 if ok else 1

    # async def cmd_run(self):
    #     await self._cmd('RUN \r')
    #     rv = await self._ans_wait()
    #     ok = rv in (b'RUN 00', b'RUN 0200')
    #     return 0 if ok else 1

    # async def cmd_sws(self, g):
    #     # STOP with STRING
    #     lat, lon, _, __ = g
    #     lat = '{:+.6f}'.format(float(lat))
    #     lon = '{:+.6f}'.format(float(lon))
    #     s = '{} {}'.format(lat, lon)
    #     c, _ = build_cmd(SWS_CMD, s)
    #     await self._cmd(c)
    #     rv = await self._ans_wait()
    #     ok = rv in (b'SWS 00', b'SWS 0200')
    #     return 0 if ok else 1
    #
    # async def cmd_rws(self, g):
    #     # RUN with STRING
    #     lat, lon, _, __ = g
    #     lat = '{:+.6f}'.format(float(lat))
    #     lon = '{:+.6f}'.format(float(lon))
    #     s = '{} {}'.format(lat, lon)
    #     c, _ = build_cmd(RWS_CMD, s)
    #     await self._cmd(c)
    #     rv = await self._ans_wait()
    #     ok = rv in (b'RWS 00', b'RWS 0200')
    #     return 0 if ok else 1

    async def cmd_gfv(self):
        await self._cmd('GFV \r')
        rv = await self._ans_wait()
        ok = len(rv) == 16 and rv.startswith(b'\n\rGFV')
        return 0 if ok else 1

    # async def cmd_dir(self) -> tuple:
    #     await self._cmd('DIR \r')
    #     rv = await self._ans_wait(timeout=3.0)
    #     if not rv:
    #         return 1, 'not'
    #     if rv == b'ERR':
    #         return 2, 'error'
    #     if rv and not rv.endswith(b'\x04\n\r'):
    #         return 3, 'partial'
    #     ls = dir_ans_to_dict(rv, '*', match=True)
    #     return 0, ls

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
