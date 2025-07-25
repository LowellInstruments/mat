import asyncio
import datetime
import json
import math
import time
from datetime import timezone
from typing import Optional
from mat.ble.ble_mat_utils import ble_mat_lowell_build_cmd as build_cmd
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from mat.li_redis import r_set
from mat.logger_controller import (
    SET_TIME_CMD,
    LOGGER_INFO_CMD,
    LOGGER_INFO_CMD_W,
    SWS_CMD,
    RWS_CMD,
    STOP_CMD,
    RUN_CMD
)
from mat.logger_controller_ble import *
from mat.utils import lowell_cmd_dir_ans_to_dict
import humanize



# =========================================
# new bleak v1.0 compliant lowell library
# this also works with old v0.2
# =========================================



class ExceptionNotConnected(Exception):
    pass
class ExceptionCommand(Exception):
    pass



GPS_FRM_STR = '{:+.6f}'
UUID_T = 'f0001132-0451-4000-b000-000000000000'
UUID_R = 'f0001131-0451-4000-b000-000000000000'
UUID_S = 'f0001130-0451-4000-b000-000000000000'
SCAN_TIMEOUT = 10
DEF_TIMEOUT_CMD = 10
DEBUG = True
g_rx = bytes()
g_cli: BleakClient
g_tag = ""



def logger_connected():
    return g_cli and g_cli.is_connected



def notification_handler(_: BleakGATTCharacteristic, bb: bytearray):
    global g_rx
    g_rx += bb



async def scan(timeout=SCAN_TIMEOUT):
    bs = BleakScanner()
    await bs.start()
    await asyncio.sleep(timeout)
    await bs.stop()
    print(bs.discovered_devices)
    # [BLEDevice(71:C5:75:B7:CB:7A, 71-C5-75-B7-CB-7A), BLEDev...
    return bs.discovered_devices



async def fast_scan(mtf, timeout=SCAN_TIMEOUT):
    # mtf: mac to find, bleak scans uppercase
    mtf = mtf.upper()
    bs = BleakScanner()
    el = time.perf_counter()

    for i in range(int(timeout)):
        await bs.start()
        await asyncio.sleep(1)
        await bs.stop()
        ls_macs = [i.address for i in bs.discovered_devices]
        try:
            idx = ls_macs.index(mtf)
            el = int(time.perf_counter() - el)
            print(f'fast_scan found mac {mtf} in {el} seconds')
            return bs.discovered_devices[idx]
        except ValueError:
            # not in list
            continue



async def connect(mac) -> Optional[bool]:
    global g_cli
    # retries are embedded in bleak library
    g_cli = BleakClient(mac, timeout=10)
    try:
        el = time.perf_counter()
        print("connecting to device...")
        await g_cli.connect()
        await g_cli.start_notify(UUID_T, notification_handler)
        el = int(time.perf_counter() - el)
        print(f"Connected in {el} seconds")
        return True
    except (Exception, ) as ex:
        print(f'error: connect {ex}')



async def disconnect():
    global g_cli
    await g_cli.disconnect()
    print('disconnected')



async def cmd(c: str, empty=True, timeout=DEF_TIMEOUT_CMD):

    async def _cmd():
        if not logger_connected():
            raise ExceptionNotConnected

        global g_tag
        g_tag = c[:3]
        if empty:
            global g_rx
            g_rx = bytes()
        if DEBUG:
            print('<-', c)
        try:
            await g_cli.write_gatt_char(UUID_R, c.encode())
            return await _wait_for_cmd_done(timeout)
        except (Exception,) as _ex:
            raise ExceptionCommand(_ex)


    try:
        return await _cmd()
    except ExceptionNotConnected:
        print(f'error: not connected to send cmd {c}')
    except ExceptionCommand as ex:
        print(f'error: sending cmd {c} -> {ex}')




def _is_cmd_done():
    c = g_tag

    if g_rx == b'ERR':
        return 1

    if c in (
        'BAT',
        'BEH',
        CONFIG_CMD,
        CRC_CMD,
        'DEL',
        'DWG',
        # no DWL
        'FDS',
        'FDG',
        'FEX',
        'GAB',
        'GDO',
        'GDX',
        'GFV',
        'GLT',
        'GSC',
        'GTM',
        'GWF',
        'HBW',
        'LED',
        'LOG',
        'MAC',
        'MTS',
        PRESSURE_SENSOR_CMD,
        TEMPERATURE_SENSOR_CMD,
        FORMAT_CMD,
        'RFN',
        'RLI',
        RUN_CMD,
        RWS_CMD,
        SET_TIME_CMD,
        'STS',
        STOP_CMD,
        SWS_CMD,
        'UTM',
        'WAK',
        'WAT',
        'WLI',
        'XOD'
    ):
        return c.encode() in g_rx

    if c in (
        'DIR'
    ):
        return g_rx.endswith(b'\x04\n\r')



async def _wait_for_cmd_done(cmd_timeout):
    # accumulate command answer in notification handler
    timeout = time.perf_counter() + cmd_timeout
    while logger_connected() and time.perf_counter() < timeout:
        await asyncio.sleep(0.2)
        if _is_cmd_done():
            print('->', g_rx)
            return g_rx

    # debug command answer when errors
    e = f'error: _wait_ans cmd {g_tag} timeout {cmd_timeout}'
    print("\033[91m {}\033[00m".format(e))
    print("\t\033[91m g_rx: {}\033[00m".format(g_rx))
    if not g_rx:
        return []

    # detect extra errors when developing mobile app
    n = int(len(g_rx) / 2)
    if g_rx[:n] == g_rx[n:]:
        print('-----------------------------------')
        e = 'error: duplicate answer {} \n' \
            'seems you used PWA recently \n' \
            'and Linux BLE stack got crazy, \n' \
            'just run $ systemctl restart bluetooth'
        print('-----------------------------------')
        print(e.format(g_rx))



# ===================================================
# list of commands for lowell instruments loggers
# ===================================================



# gets logger battery in mV
async def cmd_bat():
    rv = await cmd(f'{BAT_CMD} \r')
    ok = rv and len(rv) == 10 and rv.startswith(b'BAT')
    if not ok:
        return 1, 0
    a = rv
    if a and len(a.split()) == 2:
        # a: b'BAT 04BD08'
        _ = a.split()[1].decode()
        b = _[-2:] + _[-4:-2]
        b = int(b, 16)
        return 0, b
    return 1, 0



# sets BEHavior flags
async def cmd_beh(tag, v):
    # ex: BEH 04BCU1\r to activate connection update
    assert len(tag) == 3
    s = f'{tag}{v}'
    c, _ = build_cmd("BEH", s)
    rv = await cmd(c, timeout=5)
    if rv and rv.startswith(b'BEH'):
        return 0
    return 1



# send configuration string for DOX loggers
async def cmd_cfg(cfg_d):
    assert type(cfg_d) is dict
    s = json.dumps(cfg_d)
    c, _ = build_cmd(CONFIG_CMD, s)
    rv = await cmd(c)
    ok = rv == b'CFG 00'
    return 0 if ok else 1



# make logger calculate CRC of a file it contains
async def cmd_crc(s):
    c, _ = build_cmd(CRC_CMD, s)
    rv = await cmd(c)
    ok = rv and len(rv) == 14 and rv.startswith(b'CRC')
    if ok:
        return 0, rv[-8:].decode().lower()
    return 1, ''



# deletes a file
async def cmd_del(s):
    c, _ = build_cmd("DEL", s)
    rv = await cmd(c)
    return 0 if rv == b'DEL 00' else 1



# gets list of files in the logger
async def cmd_dir():
    rv = await cmd('DIR \r')
    if not rv:
        return 1, 'not'
    if rv == b'ERR':
        return 2, 'error'
    if rv and not rv.endswith(b'\x04\n\r'):
        return 3, 'partial'
    ls = lowell_cmd_dir_ans_to_dict(rv, '*', match=True)
    return 0, ls



# download a file in slow mode, does not use function cmd()
async def cmd_dwl(file_size) -> tuple:

    # prepare variables pre-download
    global g_rx
    g_rx = bytes()
    n = math.ceil(file_size / 2048)
    r_set('ble_dl_progress', 0)


    # loop through receiving 2048 bytes chunks
    for i in range(n):
        if not logger_connected():
            print('error: DWL not connected')
            return 1, g_rx

        try:
            c = 'DWL {:02x}{}\r'.format(len(str(i)), i)
            await g_cli.write_gatt_char(UUID_R, c.encode())
            # debug
            print(f'chunk #{i} len {len(g_rx)}')
        except (Exception,) as ex:
            print(f'error: DWL -> {ex}')
            return 1, g_rx


        # =========
        # TEST this
        # =========
        ok = 0
        for _ in range(20):
            await asyncio.sleep(.1)
            n = len(g_rx)
            ok = n == ((i + 1) * 2048) or file_size
            if ok:
                # fast quit towards next chunk
                break

        r_set('ble_dl_progress', '{:5.2f}'.format(n / file_size))
        if not ok:
            break


    rv = 0 if file_size == len(g_rx) else 1
    return rv, g_rx



# targets file to download
async def cmd_dwg(s):
    c, _ = build_cmd(DWG_FILE_CMD, s)
    rv = await cmd(c)
    return 0 if rv == b'DWG 00' else 1



# First Deployment Get, returns a date
async def cmd_fdg():
    rv = await cmd('FDG \r')
    ok = rv and len(rv) == 25 and rv.startswith(b'FDG')
    if not ok:
        return 1, ''
    return 0, rv[6:].decode()



# First Deployment Set as seconds since epoch, in UTC
async def cmd_fds():
    dt = datetime.datetime.fromtimestamp(time.time(), tz=timezone.utc)
    c, _ = build_cmd(FIRST_DEPLOYMENT_SET_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
    rv = await cmd(c)
    return 0 if rv == b'FDS 00' else 1



# does File Exists in logger
async def cmd_fex(s):
    c, _ = build_cmd(FILE_EXISTS_CMD, s)
    rv = await cmd(c)
    # return 0 == OK if file exists
    return 0 if rv == b'FEX 01' else 1



# format file-system
async def cmd_frm():
    rv = await cmd('FRM \r')
    ok = rv == b'FRM 00'
    return 0 if ok else 1


# gab: Get Accelerometer Burst
async def cmd_gab():
    c, _ = build_cmd("GAB")
    rv = await cmd(c)
    # rv: GAB C0XXYYZZXXYYZZ
    ok = rv and len(rv) == 198 and rv.startswith(b'GAB')
    if not ok:
        return 1, 0
    return 0, rv[6:]



# Get Wake flag
async def cmd_gwf():
    rv = await cmd('GWF \r')
    if rv == b'GWF 0201':
        return 0, 1
    if rv == b'GWF 0200':
        return 0, 0
    return 1, 0



# get dissolved oxygen, v1
async def cmd_gdo():
    c, _ = build_cmd(OXYGEN_SENSOR_CMD)
    rv = await cmd(c)
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



# get dissolved oxygen, v2
async def cmd_gdx():
    c, _ = build_cmd('GDX')
    rv = await cmd(c)
    # rv: b'GDX -0.03, -0.41, 17.30'
    ok = rv and rv.startswith(b'GDX') and len(rv.split(b',')) == 3
    if not ok:
        return
    a = rv[4:].decode().replace(' ', '').split(',')
    if a and len(a) == 3:
        dos, dop, dot = a
        return dos, dop, dot



# get firmware version
async def cmd_gfv():
    rv = await cmd('GFV \r')
    ok = rv and len(rv) == 12 and rv.startswith(b'GFV')
    if not ok:
        return 1, ''
    return 0, rv[6:].decode()



# get logger type
async def cmd_glt():
    rv = await cmd('GLT \r')
    ok = rv and rv in (b'GLT DO1', b'GLT DO2', b'GLT TDO', b'GLT CTD')
    # rv: b'ERR' in loggers not supporting this command
    return (0, rv.decode()[-3:]) if ok else (1, None)



# Get Sensor Conductivity
async def cmd_gsc():
    rv = await cmd('GSC \r')
    ok = rv and rv.startswith(b'GSC')
    if not ok:
        return 1, 0
    return 0, 1234



# Get Sensor Pressure
async def cmd_gsp():
    c, _ = build_cmd(PRESSURE_SENSOR_CMD)
    rv = await cmd(c)
    # rv: GSP 04ABCD
    ok = rv and len(rv) == 10 and rv.startswith(b'GSP')
    if not ok:
        return 1, 0
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



# get Sensor Temperature
async def cmd_gst():
    c, _ = build_cmd(TEMPERATURE_SENSOR_CMD)
    rv = await cmd(c)
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



# gets logger time in UTC
async def cmd_gtm():
    rv = await cmd('GTM \r')
    ok = rv and len(rv) == 25 and rv.startswith(b'GTM')
    if not ok:
        return 1, ''
    return 0, rv[6:].decode()



# has been in water
async def cmd_hbw():
    rv = await cmd('HBW \r')
    if rv == b'HBW 0201':
        return 0, 1
    if rv == b'HBW 0200':
        return 0, 0
    return 1, 0



# toggle log output generation
async def cmd_log():
    rv = await cmd(f'{LOG_EN_CMD} \r')
    if rv == b'LOG 0201':
        return 0, 1
    if rv == b'LOG 0200':
        return 0, 0
    return 1, 0



# gets logger Bluetooth mac address
async def cmd_mac():
    rv = await cmd('MAC \r')
    # rv: b'MAC 11D0:2E:AB:D9:29:48'
    ok = rv and len(rv) == 23 and rv.startswith(b'MAC')
    if ok:
        return 0, rv[6:].decode()
    return 1, ''



# makes logger blink its leds
async def cmd_led():
    rv = await cmd('LED \r')
    ok = rv == b'LED 00'
    return 0 if ok else 1



# creates a dummy file
async def cmd_mts():
    rv = await cmd('MTS \r', timeout=60)
    return 0 if rv == b'MTS 00' else 1



# request current data file name
async def cmd_rfn():
    rv = await cmd('RFN \r')
    ok = rv and rv.startswith(b'RFN')
    if not ok:
        return 1, ''
    return 0, rv[6:].decode()



# read memory area
async def cmd_rli():
    info = {}
    all_ok = True
    for each in ['SN', 'BA', 'CA']:
        print(f'RLI doing {each}')
        c, _ = build_cmd(LOGGER_INFO_CMD, each)
        # Nick wanted this timeout
        rv = await cmd(c, timeout=5)
        if not rv or rv == b'ERR':
            all_ok = False
        else:
            try:
                info[each] = rv.decode()[6:]
            except (Exception,) as ex:
                print(f'error_rli: {ex}')
                return 1, info
        await asyncio.sleep(.1)
    if all_ok:
        return 0, info
    return 1, info



# resets the logger, restarts it
async def cmd_rst():
    try:
        await g_cli.write_gatt_char(UUID_R, b'RST \r')
        time.sleep(3)
    except (Exception,) as _ex:
        print('exception during RST command')
    finally:
        return 0



# start the logger
async def cmd_run():
    rv = await cmd('RUN \r')
    ok = rv in (b'RUN 00', b'RUN 0200')
    return 0 if ok else 1



# RUN with STRING
async def cmd_rws(g):
    lat, lon, _, __ = g
    lat = GPS_FRM_STR.format(float(lat))
    lon = GPS_FRM_STR.format(float(lon))
    c, _ = build_cmd(RWS_CMD, f'{lat} {lon}')
    rv = await cmd(c, timeout=30)
    ok = rv in (b'RWS 00', b'RWS 0200')
    return 0 if ok else 1



# set logger time in UTC
async def cmd_stm():
    # time() gives seconds since epoch, in UTC
    dt = datetime.datetime.fromtimestamp(time.time(), tz=timezone.utc)
    c, _ = build_cmd(SET_TIME_CMD, dt.strftime('%Y/%m/%d %H:%M:%S'))
    rv = await cmd(c)
    return 0 if rv == b'STM 00' else 1



# stop without string
async def cmd_stp():
    rv = await cmd('STP \r', timeout=30)
    ok = rv in (b'STP 00', b'STP 0200')
    return 0 if ok else 1



# get logger status
async def cmd_sts():
    rv = await cmd('STS \r')
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



# stop with STRING
async def cmd_sws(g):
    lat, lon, _, __ = g
    lat = GPS_FRM_STR.format(float(lat))
    lon = GPS_FRM_STR.format(float(lon))
    c, _ = build_cmd(SWS_CMD, f'{lat} {lon}')
    rv = await cmd(c, timeout=30)
    ok = rv in (b'SWS 00', b'SWS 0200')
    return 0 if ok else 1



# get logger uptime in seconds
async def cmd_utm():
    rv = await cmd('UTM \r')
    ok = rv and len(rv) == 14 and rv.startswith(b'UTM')
    if ok:
        _ = rv.split()[1].decode()
        b = _[-2:] + _[-4:-2] + _[-6:-4] + _[2:4]
        t = int(b, 16)
        s = humanize.naturaldelta(datetime.timedelta(seconds=t))
        return 0, s
    return 1, ''



# sets logger WAKE flag as 1
async def cmd_wak(s):
    assert s in ('on', 'off')
    rv = await cmd(f'{WAKE_CMD} \r')
    if s == 'off' and rv == b'WAK 0200':
        return 0
    if s == 'on' and rv == b'WAK 0201':
        return 0
    # just toggle again :)
    await asyncio.sleep(.1)
    rv = await cmd(f'{WAKE_CMD} \r')
    if s == 'off' and rv == b'WAK 0200':
        return 0
    if s == 'on' and rv == b'WAK 0201':
        return 0
    return 1



# measure the Water sensor
async def cmd_wat():
    c, _ = build_cmd(WAT_CMD)
    rv = await cmd(c)
    ok = rv and len(rv) == 10 and rv.startswith(b'WAT')
    if not ok:
        return 1, 0
    a = rv
    if a and len(a.split()) == 2:
        _ = a.split()[1].decode()
        w = _[-2:] + _[-4:-2]
        w = int(w, 16)
        return 0, w
    return 1, 0



# detect logger works with liX files, an old one will return b'ERR'
async def cmd_xod():
    rv = await cmd('XOD \r')
    ok = rv and rv.endswith(b'.LIX')
    return 0 if ok else 1



# write memory area
async def cmd_wli(s):
    # s: SN1234567
    c, _ = build_cmd(LOGGER_INFO_CMD_W, s)
    rv = await cmd(c)
    ok = rv == b'WLI 00'
    return 0 if ok else 1




# async def cmd_ara():
#     # adjust rate advertisement logger
#     await cmd('ARA \r')
#     rv = await self._ans_wait()
#     # rv: b'ARA 0200'
#     ok = rv and len(rv) == 8 and rv.startswith(b'ARA')
#     if ok:
#         return 0, int(rv.decode()[-1])
#     return 1, 0
#
#
# async def cmd_arf():
#     # adjust rate advertisement fast for 1 minute
#     await cmd('ARF \r')
#     rv = await self._ans_wait()
#     # rv: b'ARF 0200'
#     ok = rv and len(rv) == 8 and rv.startswith(b'ARF')
#     if ok:
#         return 0, int(rv.decode()[-1])
#     return 1, 0


# async def cmd_scc(tag, v):
#     # Set Calibration Constants, for PRA, PRB...
#     assert len(tag) == 3
#     assert len(v) == 5
#     s = '{}{}'.format(tag, v)
#     c, _ = build_cmd(SET_CALIBRATIONcmd, s)
#     await cmd(c)
#     rv = await self._ans_wait(timeout=30)
#     return 0 if rv == b'SCC 00' else 1
#
#
# async def cmd_scf(tag, v):
#     # Set Calibration proFiling, for profiling
#     assert len(tag) == 3
#     assert len(v) == 5
#     s = '{}{}'.format(tag, v)
#     c, _ = build_cmd(SET_PRF_CONFIGURATIONcmd, s)
#     await cmd(c)
#     rv = await self._ans_wait(timeout=30)
#     return 0 if rv == b'SCF 00' else 1
#
#
# async def cmd_ssp(v):
#     # Set Sensor Pressure, for debugging and developing
#     v = str(v).zfill(5)
#     c, _ = build_cmd('SSP', v)
#     await cmd(c)
#     rv = await self._ans_wait(timeout=5)
#     return 0 if rv == b'SSP 00' else 1
#
# async def cmd_spn(v):
#     # Set Pressure Number, for profiling
#     assert 0 < v < 9
#     await cmd('SPN 01{}\r'.format(v))
#     rv = await self._ans_wait()
#     ok = rv and len(rv) == 7 and rv.startswith(b'SPN')
#     if not ok:
#         return 1, ''
#     return 0, rv[6:].decode()
#

#
# async def cmd_dha():
#     await cmd('DHA \r')
#     rv = await self._ans_wait()
#     ok = rv == b'DHA 00'
#     return 0 if ok else 1
#
#
#
# async def cmd_dns(s):
#     # stands for Deployment Name Set
#     assert len(s) == 3
#     c, _ = build_cmd(DEPLOYMENT_NAME_SETcmd, s)
#     await cmd(c)
#     rv = await self._ans_wait()
#     ok = rv == b'DNS 00'
#     return 0 if ok else 1
#
#
# async def cmd_dng():
#     # stands for Deployment Name Get
#     c, _ = build_cmd(DEPLOYMENT_NAME_GETcmd)
#     await cmd(c)
#     rv = await self._ans_wait()
#     ok = rv and len(rv) == 9 and rv.startswith(b'DNG')
#     if not ok:
#         return 1, ''
#     return 0, rv[6:].decode()
#
#

#
#
# async def cmd_bna():
#     c, _ = build_cmd('BNA')
#     await cmd(c)
#     rv = await self._ans_wait()
#     ok = rv and len(rv) == 6 and rv.startswith(b'BNA 00')
#     if ok:
#         return 0
#     return 1
#
#

#
#

#

#
# async def cmd_tst():
#     c, _ = build_cmd('TST')
#     await cmd(c)
#     rv = await self._ans_wait(timeout=60)
#     if rv == b'TST 0200':
#         return 0
#     return 1
#
#
# async def cmd_tsl():
#     c, _ = build_cmd('TSL')
#     await cmd(c)
#     rv = await self._ans_wait(timeout=600)
#     if rv == b'TSL 0200':
#         return 0
#     return 1
#
#
# async def cmd_oad_erase():
#     c, _ = build_cmd('OAE')
#     await cmd(c)
#     rv = await self._ans_wait(timeout=45)
#     if rv == b'OAE 0200':
#         return 0
#     return 1
#
#
# async def cmd_oad_factory():
#     c, _ = build_cmd('OAF')
#     await cmd(c)
#     rv = await self._ans_wait(timeout=45)
#     if rv == b'OAF 0200':
#         return 0
#     return 1


# async def cmd_gcc():
#     # Get Calibration Constants
#     await cmd('GCC \r')
#     rv = await self._ans_wait()
#     # n: number of fields of cc_area
#     # in last version, n = 33
#     # in version v3987, n = 29
#     n = 33
#     ok = rv and len(rv) == ((n * 5) + 6) and rv.startswith(b'GCC')
#     if ok:
#         return 0, rv.decode()
#     if rv:
#         print(f'error: bad GCC length {len(rv)} - 6 != {n} - 6')
#     else:
#         print(f'error: bad GCC length = None')
#     return 1, ""
#
#
# async def cmd_gcf():
#     # Get constants proFiling
#     await cmd('GCF \r')
#     rv = await self._ans_wait()
#     # n: number of fields of cf_area
#     # in last version, n = 9
#     # in version v3987, n = 13
#     n = 9
#     ok = rv and len(rv) == ((n * 5) + 6) and rv.startswith(b'GCF')
#     if ok:
#         return 0, rv.decode()
#     return 1, ""
#
#
# async def cmd_gwc():
#     # Get Water Column (up, down...)
#     await cmd('GWC \r')
#     rv = await self._ans_wait()
#     ok = rv and rv.startswith(b'GWC')
#     if ok:
#         return 0, rv.decode()
#     return 1, ""
#

#
#

# async def cmd_per():
#     # Get Profiling Error, for debugging
#     await cmd('PER \r')
#     rv = await self._ans_wait(timeout=10)
#     if rv and len(rv) == 8:
#         return 0, rv.decode()[6:]
#     return 1, None
#
#


#
# async def cmd_ddh_a(g) -> tuple:
#     lat, lon, _, __ = g
#     lat = GPS_FRM_STR.format(float(lat))
#     lon = GPS_FRM_STR.format(float(lon))
#     c, _ = build_cmd('__A', f'{lat} {lon}')
#     await cmd(c)
#     rv = await self._ans_wait(timeout=30)
#     if not rv:
#         return 1, 'not'
#     if rv == b'ERR':
#         return 2, 'error'
#     if rv and not rv.endswith(b'\x04\n\r'):
#         return 3, 'partial'
#     ls = lowellcmd_dir_ans_to_dict(rv, '*', match=True)
#     return 0, ls
#
#
# async def cmd_ddh_b(rerun):
#     # time() -> seconds since epoch, in UTC
#     rerun = int(rerun)
#     dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
#     print(f"debug: DDB sent {rerun}{dt.strftime('%Y/%m/%d %H:%M:%S')}")
#     c, _ = build_cmd('__B', f"{rerun}{dt.strftime('%Y/%m/%d %H:%M:%S')}")
#     await cmd(c)
#     rv = await self._ans_wait()
#     ok = rv and rv.startswith(b'__B')
#     if ok:
#         return 0, rv
#     return 1, bytes()
#
#

#
#
# async def cmd_dwf(z, ip=None, port=None) -> tuple:
#     # z: file size
#     self.ans = bytes()
#     ble_mat_progress_dl(0, z, ip, port)
#     timeout_z = 0
#
#     # send DWF command
#     c = 'DWF \r'
#     await cmd(c)
#
#     # receive the WHOLE file
#     while 1:
#         await asyncio.sleep(.5)
#
#         # doesn't affect download speed
#         if not await self.is_connected():
#             print('error: DWF disconnected while receiving file')
#             return 1, bytes()
#
#         # the FAST download is going well
#         ble_mat_progress_dl(len(self.ans), z, ip, port)
#         if len(self.ans) == z:
#             print('all file received')
#             # receive the last shit
#             break
#
#         # check for stall
#         if len(self.ans) == timeout_z:
#             print('error DWF timeout')
#             break
#         timeout_z = len(self.ans)
#
#     print('z', z)
#     print('len(self.ans)', len(self.ans))
#     rv = 0 if z == len(self.ans) else 1
#     return rv, self.ans







async def main():

    rv = r_set('ble_dl_progress', 0)
    print(rv)
    return

    # mac_test = "D0:2E:AB:D9:29:48" # TDO
    mac_test = "F0:5E:CD:25:95:E0" # CTD

    print("starting scan...")
    await fast_scan(mac_test)
    rv = await connect(mac_test)
    if not rv:
        return

    # rv = await cmd_stm()
    # print(rv)
    # rv = await cmd_sts()
    # print(rv)
    # rv = await cmd_frm()
    # print(rv)
    # rv = await cmd_dir()
    # print(rv)
    # rv = await cmd_gsp()
    # print(rv)
    # rv = await cmd_gst()
    # print(rv)
    # rv = await cmd_mts()
    # print(rv)
    # rv = await cmd_gfv()
    # print(rv)
    # rv = await cmd_glt()
    # print(rv)
    # rv = await cmd_gsc()
    # print(rv)
    # rv = await cmd_beh('BCU',  1)
    # print(rv)
    # rv = await cmd_mac()
    # print(rv)

    # rv = await cmd_dwg('dummy_946706414.lid')
    # print(rv)
    # rv = await cmd_dwg('dummy_94670641422.lid')
    # print(rv)

    # rv = await cmd_hbw()
    # print(rv)
    # rv = await cmd_log()
    # print(rv)
    # rv = await cmd_bat()
    # print(rv)
    # rv = await cmd_fex('pepilid')
    # print(rv)
    # rv = await cmd_wli("SN1234567")
    # print(rv)

    # rv = await cmd_rli()
    # print(rv)

    # rv = await cmd_dir()
    # print(rv)


    rv = await cmd_dwg('dummy_1753219635.lid')
    print(rv)

    rv = await cmd_dwl(77950)
    print(rv)


    # for i in range(100):
    #     rv = await cmd_gsc()
    #     print(rv)
    #     if not rv:
    #         print('error during command')
    #         break
    #     time.sleep(3)


    await disconnect()



if __name__ == "__main__":
    asyncio.run(main())
