import asyncio
import json
import platform
from datetime import datetime, timezone, timedelta
import math
import time
import humanize
from bleak import BleakError, BleakClient
from mat.ble.ble_mat_utils import ble_mat_lowell_build_cmd as build_cmd, \
    ble_mat_progress_dl, \
    ble_mat_hci_exists
from mat.ble.bleak.cc26x2r_ans import is_cmd_done
from mat.logger_controller import SET_TIME_CMD, DEL_FILE_CMD, SWS_CMD, RWS_CMD, LOGGER_INFO_CMD_W, \
    LOGGER_INFO_CMD
from mat.logger_controller_ble import DWG_FILE_CMD, CRC_CMD, CONFIG_CMD, WAKE_CMD, OXYGEN_SENSOR_CMD, BAT_CMD, \
    FILE_EXISTS_CMD, WAT_CMD, LOG_EN_CMD, SET_CALIBRATION_CMD, \
    DEPLOYMENT_NAME_SET_CMD, DEPLOYMENT_NAME_GET_CMD, FIRST_DEPLOYMENT_SET_CMD, PRESSURE_SENSOR_CMD, \
    TEMPERATURE_SENSOR_CMD, SET_PRF_CONFIGURATION_CMD
from mat.utils import lowell_cmd_dir_ans_to_dict, linux_is_rpi


UUID_T = 'f0001132-0451-4000-b000-000000000000'
UUID_R = 'f0001131-0451-4000-b000-000000000000'
GPS_FRM_STR = '{:+.6f}'


class BleCC26X2:    # pragma: no cover
    def __init__(self, h='hci0', dbg_ans=False):
        self.cli = None
        self.ans = bytes()
        self.tag = ''
        self.dbg_ans = dbg_ans
        if platform.system() == 'Linux':
            assert h.startswith('hci')
            ble_mat_hci_exists(h)
        self.h = h

    async def is_connected(self):
        return self.cli and await self.cli.is_connected()

    async def _cmd(self, c: str, empty=True):
        self.tag = c[:3]
        if empty:
            # clean the answer buffer, or not
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
                # print('debug self.ans -> ', self.ans)
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
        print(f'[ BLE ] timeout {elapsed} for cmd {self.tag}')
        print('\t dbg_ans:', self.ans)
        if not self.ans:
            return

        # detect extra errors :)
        n = int(len(self.ans) / 2)
        if self.ans[:n] == self.ans[n:]:
            print('-----------------------------------')
            e = 'error duplicate answer: {} \n' \
                'seems you used PWA recently \n' \
                'and Linux BLE stack got crazy, \n' \
                'just run $ systemctl restart bluetooth'
            print('-----------------------------------')
            print(e.format(self.ans))

    async def cmd_stm(self):
        # time() -> seconds since epoch, in UTC
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        c, _ = build_cmd(SET_TIME_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'STM 00' else 1

    async def cmd_xod(self):
        # detect logger works with liX files, an old one will return b'ERR'
        await self._cmd('XOD \r')
        rv = await self._ans_wait()
        # rv: b'XOD 04.LIX'
        ok = rv and rv.endswith(b'.LIX')
        return 0 if ok else 1

    async def cmd_ara(self):
        # adjust rate advertisement logger
        await self._cmd('ARA \r')
        rv = await self._ans_wait()
        # rv: b'ARA 0200'
        ok = rv and len(rv) == 8 and rv.startswith(b'ARA')
        if ok:
            return 0, int(rv.decode()[-1])
        return 1, 0

    async def cmd_arf(self):
        # adjust rate advertisement fast for 1 minute
        await self._cmd('ARF \r')
        rv = await self._ans_wait()
        # rv: b'ARF 0200'
        ok = rv and len(rv) == 8 and rv.startswith(b'ARF')
        if ok:
            return 0, int(rv.decode()[-1])
        return 1, 0

    async def cmd_arp(self):
        # adjust rate tx power logger
        await self._cmd('ARP \r')
        rv = await self._ans_wait()
        # rv: b'ARP 0201'
        ok = rv and len(rv) == 8 and rv.startswith(b'ARP')
        if ok:
            return 0, int(rv.decode()[-1])
        return 1, 0

    async def cmd_fds(self):
        """
        stands for first Deployment Set
        :return: 0 if went OK
        """
        # time() -> seconds since epoch, in UTC
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        c, _ = build_cmd(FIRST_DEPLOYMENT_SET_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'FDS 00' else 1

    async def cmd_dwg(self, s):
        c, _ = build_cmd(DWG_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        return 0 if rv == b'DWG 00' else 1

    async def cmd_crc(self, s):
        c, _ = build_cmd(CRC_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=60)
        ok = rv and len(rv) == 14 and rv.startswith(b'CRC')
        if ok:
            return 0, rv[-8:].decode().lower()
        return 1, ''

    async def cmd_del(self, s):
        c, _ = build_cmd(DEL_FILE_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        return 0 if rv == b'DEL 00' else 1

    async def cmd_scc(self, tag, v):
        # Set Calibration Constants, for PRA, PRB...
        assert len(tag) == 3
        assert len(v) == 5
        s = '{}{}'.format(tag, v)
        c, _ = build_cmd(SET_CALIBRATION_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        return 0 if rv == b'SCC 00' else 1

    async def cmd_beh(self, tag, v):
        assert len(tag) == 3
        s = f'{tag}{v}'
        c, _ = build_cmd("BEH", s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=5)
        if rv and rv.startswith(b'BEH'):
            return 0
        return 1

    async def cmd_scf(self, tag, v):
        # Set Calibration proFiling, for profiling
        assert len(tag) == 3
        assert len(v) == 5
        s = '{}{}'.format(tag, v)
        c, _ = build_cmd(SET_PRF_CONFIGURATION_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        return 0 if rv == b'SCF 00' else 1

    async def cmd_ssp(self, v):
        # Set Sensor Pressure, for debugging and developing
        v = str(v).zfill(5)
        c, _ = build_cmd('SSP', v)
        await self._cmd(c)
        rv = await self._ans_wait(timeout=5)
        return 0 if rv == b'SSP 00' else 1

    async def cmd_fex(self, s):
        # does File EXists in logger
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

    async def cmd_rfn(self):
        await self._cmd('RFN \r')
        rv = await self._ans_wait()
        ok = rv and rv.startswith(b'RFN')
        if not ok:
            return 1, ''
        return 0, rv[6:].decode()

    async def cmd_fdg(self):
        # First Deployment Get, returns a date
        await self._cmd('FDG \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 25 and rv.startswith(b'FDG')
        if not ok:
            return 1, ''
        return 0, rv[6:].decode()

    async def cmd_spn(self, v):
        # Set Pressure Number, for profiling
        assert 0 < v < 9
        await self._cmd('SPN 01{}\r'.format(v))
        rv = await self._ans_wait()
        ok = rv and len(rv) == 7 and rv.startswith(b'SPN')
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

    async def cmd_dha(self):
        await self._cmd('DHA \r')
        rv = await self._ans_wait()
        ok = rv == b'DHA 00'
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

    async def cmd_dns(self, s):
        # stands for Deployment Name Set
        assert len(s) == 3
        c, _ = build_cmd(DEPLOYMENT_NAME_SET_CMD, s)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv == b'DNS 00'
        return 0 if ok else 1

    async def cmd_dng(self):
        # stands for Deployment Name Get
        c, _ = build_cmd(DEPLOYMENT_NAME_GET_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and len(rv) == 9 and rv.startswith(b'DNG')
        if not ok:
            return 1, ''
        return 0, rv[6:].decode()

    async def cmd_gdo(self):
        # old GDO command, see GDX
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

    async def cmd_gdx(self):
        # new command for Get Dissolved Oxygen
        c, _ = build_cmd('GDX')
        await self._cmd(c)
        rv = await self._ans_wait()
        # rv: b'GDX -0.03, -0.41, 17.30'
        ok = rv and rv.startswith(b'GDX') and len(rv.split(b',')) == 3
        if not ok:
            return
        a = rv[4:].decode().replace(' ', '').split(',')
        if a and len(a) == 3:
            dos, dop, dot = a
            return dos, dop, dot

    async def cmd_bna(self):
        c, _ = build_cmd('BNA')
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and len(rv) == 6 and rv.startswith(b'BNA 00')
        if ok:
            return 0
        return 1

    async def cmd_gsp(self):
        # Get Sensor Pressure
        c, _ = build_cmd(PRESSURE_SENSOR_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        # rv: GSP 04ABCD
        ok = rv and len(rv) == 10 and rv.startswith(b'GSP')
        if not ok:
            return
        a = rv
        if a and len(a.split()) == 2:
            # a: b'GSP 043412'
            _ = a.split()[1].decode()
            p = _[2:6]
            # p: '3412' --> '1234'
            p = p[-2:] + p[:2]
            p = int(p, 16)
            return 0, p
        return 1, 0

    async def cmd_gst(self):
        # gst: Get Sensor Temperature
        c, _ = build_cmd(TEMPERATURE_SENSOR_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        # rv: GST 04ABCD
        ok = rv and len(rv) == 10 and rv.startswith(b'GST')
        if not ok:
            return
        a = rv
        # a: b'GST 043412'
        if a and len(a.split()) == 2:
            _ = a.split()[1].decode()
            t = _[2:6]
            # t: '3412' --> '1234'
            t = t[-2:] + t[:2]
            t = int(t, 16)
            return 0, t
        return 1, 0

    async def cmd_gsc(self):
        # gst: Get Sensor Conductivity
        c, _ = build_cmd('GSC')
        await self._cmd(c)
        time.sleep(1)
        return 0, 1000

    async def cmd_gab(self):
        # gab: Get Accelerometer Burst
        c, _ = build_cmd("GAB")
        await self._cmd(c)
        rv = await self._ans_wait()
        # rv: GAB C0XXYYZZXXYYZZ
        ok = rv and len(rv) == 198 and rv.startswith(b'GAB')
        if not ok:
            return 1, 0
        return 0, rv[6:]

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
        # measure the Water sensor
        c, _ = build_cmd(WAT_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and len(rv) == 10 and rv.startswith(b'WAT')
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
        # (de-)activate Wake mode
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

    async def cmd_gwf(self):
        # Get Wake flag
        c, _ = build_cmd('GWF')
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'GWF 0201':
            return 0, 1
        if rv == b'GWF 0200':
            return 0, 0
        return 1, 0

    async def cmd_log(self):
        c, _ = build_cmd(LOG_EN_CMD)
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'LOG 0201':
            return 0, 1
        if rv == b'LOG 0200':
            return 0, 0
        return 1, 0

    async def cmd_hbw(self):
        c, _ = build_cmd("HBW")
        await self._cmd(c)
        rv = await self._ans_wait()
        if rv == b'HBW 0201':
            return 0, 1
        if rv == b'HBW 0200':
            return 0, 0
        return 1, 0

    async def cmd_tst(self):
        c, _ = build_cmd('TST')
        await self._cmd(c)
        rv = await self._ans_wait(timeout=60)
        if rv == b'TST 0200':
            return 0
        return 1

    async def cmd_tsl(self):
        c, _ = build_cmd('TSL')
        await self._cmd(c)
        rv = await self._ans_wait(timeout=600)
        if rv == b'TSL 0200':
            return 0
        return 1

    async def cmd_oad_erase(self):
        c, _ = build_cmd('OAE')
        await self._cmd(c)
        rv = await self._ans_wait(timeout=45)
        if rv == b'OAE 0200':
            return 0
        return 1

    async def cmd_oad_factory(self):
        c, _ = build_cmd('OAF')
        await self._cmd(c)
        rv = await self._ans_wait(timeout=45)
        if rv == b'OAF 0200':
            return 0
        return 1

    async def cmd_rli(self):
        info = {}
        all_ok = True
        for each in ['SN', 'BA', 'CA']:
            print('RLI doing', each)
            c, _ = build_cmd(LOGGER_INFO_CMD, each)
            await self._cmd(c)
            # Nick wanted this timeout
            rv = await self._ans_wait(timeout=5.0)
            if not rv or rv == b'ERR':
                all_ok = False
            else:
                try:
                    info[each] = rv.decode()[6:]
                except (Exception, ) as ex:
                    print(f'error_rli: {ex}')
                    return 1, info
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
            return 0, state
        return 1, 'error'

    async def cmd_gcc(self):
        # Get Calibration Constants
        await self._cmd('GCC \r')
        rv = await self._ans_wait()
        # n: number of fields of cc_area
        # in last version, n = 33
        # in version v3987, n = 29
        n = 33
        ok = rv and len(rv) == ((n * 5) + 6) and rv.startswith(b'GCC')
        if ok:
            return 0, rv.decode()
        if rv:
            print(f'error: bad GCC length {len(rv)} - 6 != {n} - 6')
        else:
            print(f'error: bad GCC length = None')
        return 1, ""

    async def cmd_gcf(self):
        # Get constants proFiling
        await self._cmd('GCF \r')
        rv = await self._ans_wait()
        # n: number of fields of cf_area
        # in last version, n = 9
        # in version v3987, n = 13
        n = 9
        ok = rv and len(rv) == ((n * 5) + 6) and rv.startswith(b'GCF')
        if ok:
            return 0, rv.decode()
        return 1, ""

    async def cmd_gwc(self):
        # Get Water Column (up, down...)
        await self._cmd('GWC \r')
        rv = await self._ans_wait()
        ok = rv and rv.startswith(b'GWC')
        if ok:
            return 0, rv.decode()
        return 1, ""

    async def cmd_run(self):
        await self._cmd('RUN \r')
        rv = await self._ans_wait(timeout=30)
        ok = rv in (b'RUN 00', b'RUN 0200')
        return 0 if ok else 1

    async def cmd_mts(self):
        await self._cmd('MTS \r')
        rv = await self._ans_wait(timeout=60)
        return 0 if rv == b'MTS 00' else 1

    async def cmd_per(self):
        # Get Profiling Error, for debugging
        await self._cmd('PER \r')
        rv = await self._ans_wait(timeout=10)
        if rv and len(rv) == 8:
            return 0, rv.decode()[6:]
        return 1, None

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

    async def cmd_glt(self):
        c, _ = build_cmd('GLT')
        await self._cmd(c)
        rv = await self._ans_wait(timeout=2)
        ok = rv in (b'GLT DO1', b'GLT DO2', b'GLT TDO', b'GLT ???')
        # rv: b'ERR' in loggers not supporting this command
        return (0, rv.decode()[-3:]) if ok else (1, None)

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

    async def cmd_rst(self):
        await self._cmd('RST \r')
        await asyncio.sleep(3)
        return 0

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

    async def cmd_ddh_a(self, g) -> tuple:
        lat, lon, _, __ = g
        lat = GPS_FRM_STR.format(float(lat))
        lon = GPS_FRM_STR.format(float(lon))
        c, _ = build_cmd('__A', f'{lat} {lon}')
        await self._cmd(c)
        rv = await self._ans_wait(timeout=30)
        if not rv:
            return 1, 'not'
        if rv == b'ERR':
            return 2, 'error'
        if rv and not rv.endswith(b'\x04\n\r'):
            return 3, 'partial'
        ls = lowell_cmd_dir_ans_to_dict(rv, '*', match=True)
        return 0, ls

    async def cmd_ddh_b(self, rerun):
        # time() -> seconds since epoch, in UTC
        rerun = int(rerun)
        dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
        print(f"debug, DDB sent {rerun}{dt.strftime('%Y/%m/%d %H:%M:%S')}")
        c, _ = build_cmd('__B', f"{rerun}{dt.strftime('%Y/%m/%d %H:%M:%S')}")
        await self._cmd(c)
        rv = await self._ans_wait()
        ok = rv and rv.startswith(b'__B')
        if ok:
            return 0, rv
        return 1, bytes()

    async def cmd_dwl(self, z, ip=None, port=None) -> tuple:
        # z: file size
        self.ans = bytes()
        n = math.ceil(z / 2048)
        ble_mat_progress_dl(0, z, ip, port)

        for i in range(n):
            c = 'DWL {:02x}{}\r'.format(len(str(i)), i)
            await self._cmd(c, empty=False)
            for _ in range(40):
                # 40 == 8 seconds
                await self._ans_wait(timeout=.2)
                if len(self.ans) == (i + 1) * 2048:
                    break
                if len(self.ans) == z:
                    break
            ble_mat_progress_dl(len(self.ans), z, ip, port)
            # print('chunk #{} len {}'.format(i, len(self.ans)))

        rv = 0 if z == len(self.ans) else 1
        return rv, self.ans

    async def cmd_dwf(self, z, ip=None, port=None) -> tuple:

        # z: file size
        self.ans = bytes()
        ble_mat_progress_dl(0, z, ip, port)
        timeout_z = 0

        # send DWF command
        c = 'DWF \r'
        await self._cmd(c)

        # receive the WHOLE file
        while 1:
            await asyncio.sleep(.5)

            # doesn't affect download speed
            if not await self.is_connected():
                print('error: DWF disconnected while receiving file')
                return 1, bytes()

            # the FAST download is going well
            ble_mat_progress_dl(len(self.ans), z, ip, port)
            if len(self.ans) == z:
                print('all file received')
                # receive the last shit
                break

            # check for stall
            if len(self.ans) == timeout_z:
                print('error DWF timeout')
                break
            timeout_z = len(self.ans)

        print('z', z)
        print('len(self.ans)', len(self.ans))
        rv = 0 if z == len(self.ans) else 1
        return rv, self.ans


    async def cmd_utm(self):
        # command Uptime
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

    async def cmd_rtm(self):
        # command Runtime
        await self._cmd('RTM \r')
        rv = await self._ans_wait()
        ok = rv and len(rv) == 14 and rv.startswith(b'RTM')
        if ok:
            _ = self.ans.split()[1].decode()
            b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
            t = int(b, 16)
            s = humanize.naturaldelta(timedelta(seconds=t))
            return 0, s
        return 1, ''

    async def cmd_mac(self):
        # command get mac
        await self._cmd('MAC \r')
        rv = await self._ans_wait()
        # rv: b'MAC 11D0:2E:AB:D9:29:48'
        ok = rv and len(rv) == 23 and rv.startswith(b'MAC')
        if ok:
            return 0, rv[6:].decode()
        return 1, ''

    async def disconnect(self):
        try:
            await self.cli.disconnect()
        except (Exception, ):
            pass

    # --------------------
    # connection routine
    # --------------------

    # async def _connect_rpi(self, mac):
    #     def c_rx(_: int, b: bytearray):
    #         self.ans += b
    #
    #     till = time.perf_counter() + 30
    #     h = self.h
    #     self.cli = BleakClient(mac, adapter=h)
    #     rv: int
    #
    #     while True:
    #         now = time.perf_counter()
    #         if now > till:
    #             print('_connect_rpi totally failed')
    #             rv = 1
    #             break
    #
    #         try:
    #             if await self.cli.connect():
    #                 await self.cli.start_notify(UUID_T, c_rx)
    #                 rv = 0
    #                 break
    #
    #         except (asyncio.TimeoutError, BleakError, OSError) as ex:
    #             _ = int(till - time.perf_counter())
    #             print(f'_connect_rpi failed, {_} seconds left -> {ex}')
    #             await asyncio.sleep(.5)
    #
    #     return rv

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

    # -------------------------------------------
    # slightly changed this fxn on 2024, Aug. 26
    # -------------------------------------------
    async def _connect_rpi(self, mac):
        def c_rx(_: int, b: bytearray):
            self.ans += b

        till = time.perf_counter() + 30
        h = self.h
        rv: int

        while True:
            now = time.perf_counter()
            if now > till:
                print('_connect_rpi totally failed by timeout')
                return 1

            try:
                self.cli = BleakClient(mac, adapter=h)
                if await self.cli.connect():
                    await self.cli.start_notify(UUID_T, c_rx)
                    return 0

            except (asyncio.TimeoutError, BleakError, OSError) as ex:
                _ = int(till - time.perf_counter())
                print(f'_connect_rpi failed, {_} seconds left -> {ex}')
                await asyncio.sleep(1)

        # probably unreachable
        return 2

    async def connect(self, mac):
        if linux_is_rpi():
            rv = await self._connect_rpi(mac)
            return rv

        # when not Raspberry
        return await self._connect(mac)
