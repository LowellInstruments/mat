import asyncio
import platform
from datetime import datetime, timezone
import time
from bleak import BleakError, BleakClient
from mat.ble.ble_mat_utils import ble_mat_lowell_build_cmd as build_cmd, \
    ble_mat_bluetoothctl_disconnect, ble_mat_hci_exists
from mat.ble.bleak.rn4020_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD
from mat.logger_controller_ble import GET_FILE_CMD
from mat.utils import lowell_cmd_dir_ans_to_dict


UUID_T = UUID_R = '00035b03-58e6-07dd-021a-08123a000301'


class BleRN4020Base:
    """
    never to be used directly but BleRN4020
    """

    def __init__(self, h='hci0'):
        self.cli = None
        self.ans = bytes()
        self.tag = ''
        if platform.system() == 'Linux':
            assert h.startswith('hci')
            ble_mat_hci_exists(h)
        self.h = h
        ble_mat_bluetoothctl_disconnect()

    async def _cmd(self, c: str, empty=True):
        self.tag = c[:3]
        if empty:
            self.ans = bytes()
        print('<-', c)
        for i in c:
            await self.cli.write_gatt_char(UUID_R, i.encode())
            await asyncio.sleep(.01)

    async def _ans_wait(self, timeout=10.0):

        while self.cli and self.cli.is_connected:
            # evaluate here, not in loop condition
            if timeout <= 0:
                break

            # accumulate in notification handler
            await asyncio.sleep(0.1)
            timeout -= 0.1

            # see if no more to receive
            if is_cmd_done(self.tag, self.ans):
                print('->', self.ans)
                return self.ans

        print('[ BLE ] timeout -> cmd {}'.format(self.tag))

    async def cmd_stm(self):
        # time() -> seconds since epoch, in UTC
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        c, _ = build_cmd(SET_TIME_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'\n\rSTM 00\r\n' else 1

    async def cmd_del(self, s):
        c, _ = build_cmd(DEL_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        # this one is a bit different
        return 0 if rv and rv.endswith(b'DEL 00\r\n') else 1

    async def cmd_gtm(self):
        await self._cmd('GTM \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 29 and rv.startswith(b'\n\rGTM')
        if ok:
            return 0, rv
        return 1, rv

    async def cmd_btc(self):
        c = 'BTC 00T,0006,0000,0064\r'
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv:
            return 0
        return 1

    async def cmd_stp(self):
        await self._cmd('STP \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 12 and rv.startswith(b'\n\rSTP')
        return 0 if ok else 1

    async def cmd_run(self):
        await self._cmd('RUN \r')
        rv = await self._ans_wait()
        return 0 if rv == b'\n\rRUN 00\r\n' else 1

    async def cmd_rfn(self):
        await self._cmd('RFN \r')
        rv = await self._ans_wait()
        if not rv:
            return 1, ''
        rv = rv.replace(b'\r', b'')
        rv = rv.replace(b'\n', b'')
        # only .lid name file remains
        return 0, rv.decode()

    async def cmd_sws(self, g):
        # STOP with STRING
        lat, lon, _, __ = g
        lat = '{:+.6f}'.format(float(lat))
        lon = '{:+.6f}'.format(float(lon))
        s = '{} {}'.format(lat, lon)
        c, _ = build_cmd(SWS_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'\n\rSWS 0200\r\n' else 1

    @staticmethod
    async def cmd_rws(_):
        # does not exist for RN4020 loggers
        assert False

    async def cmd_gfv(self):
        await self._cmd('GFV \r')
        rv = await self._ans_wait()
        if rv:
            return 0, rv
        return 1, rv

    async def cmd_get(self, s):
        c, _ = build_cmd(GET_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'\n\rGET 00\r\n' else 1

    async def cmd_dir(self) -> tuple:
        await self._cmd('DIR \r')
        rv = await self._ans_wait()
        if not rv:
            return 1, 'not'
        if rv == b'ERR':
            return 2, 'error'
        if rv and not rv.endswith(b'\x04\n\r'):
            return 3, 'partial'
        ls = lowell_cmd_dir_ans_to_dict(rv, '*', match=True)
        return 0, ls

    async def disconnect(self):
        if self.cli and self.cli.is_connected:
            await self.cli.disconnect()

    async def connect(self, mac):
        def c_rx(_: int, b: bytearray):
            self.ans += b

        for i in range(3):
            try:
                # we pass hci here
                h = self.h
                self.cli = BleakClient(mac, adapter=h)
                if await self.cli.connect():
                    await self.cli.start_notify(UUID_T, c_rx)
                    return 0
            except (asyncio.TimeoutError, BleakError, OSError):
                print('connection attempt {} of 3 failed'.format(i + 1))
                time.sleep(1)
        return 1

    async def cmd_xmodem(self, z):
        # should never be called, dynamically resolves to a method
        # in superclass BleRN4020
        print('cmd_xmodem should never be called')
        return 1, bytes()
