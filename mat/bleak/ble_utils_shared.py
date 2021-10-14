import asyncio
import subprocess as sp

import crc16
from packaging import version
import platform
from bleak import BleakClient, BleakScanner

from mat.data_converter import default_parameters, DataConverter

ENGINE_CMD_BYE = 'cmd_bye'
ENGINE_CMD_CON = 'cmd_connect'
ENGINE_CMD_DISC = 'cmd_disconnect'
ENGINE_CMD_SCAN = 'cmd_scan'
ENGINE_CMD_EXC = 'exc_ble_engine'


g_ans = bytes()
g_cmd = ''
g_hooks = {
    'uuid_c': '',
    'cmd_cb': None,
    'ans_cb': None
}


def check_bluez_version():
    # cannot check bluez on non-linux platforms
    if not platform.system() in ('Linux', 'linux'):
        return True

    # old bluez give 'write not permitted' errors
    # when working with RN4020 loggers
    s = 'bluetoothctl -v'
    rv = sp.run(s, shell=True, stdout=sp.PIPE)
    v = rv.stdout.decode()
    v = v.replace('bluetoothctl: ', '')
    v = v.replace('\n', '')
    return version.parse(v) >= version.parse('5.61')


def xmd_frame_check_crc(b):
    data = b[3:-2]
    rx_crc = b[-2:]
    calc_crc_int = crc16.crc16xmodem(data)
    calc_crc_bytes = calc_crc_int.to_bytes(2, byteorder='big')
    return calc_crc_bytes == rx_crc


def utils_mat_convert_data(data, path, size):
    if data == b'':
        return False
    try:
        with open(path, 'wb') as f:
            f.write(data)
            f.truncate(size)
        pars = default_parameters()
        converter = DataConverter(path, pars)
        converter.convert()
        return True
    except Exception as ex:
        print(ex)
        return False


async def engine_parse_cmd_bye(c, cli, q):
    if c == ENGINE_CMD_BYE:
        if cli:
            await cli.disconnect()
        q.put(b'bye OK')
        return True


async def engine_parse_xmodem(c):
    return c[:4] == b'XMD '


def engine_parse_cmd_exception(c):
    if c.startswith(ENGINE_CMD_EXC):
        raise EngineException(ENGINE_CMD_EXC)


def engine_parse_cmd_disconnect(c, q):
    if c.startswith(ENGINE_CMD_DISC):
        q.put(b'disconnect OK')
        return True


def engine_parse_cmd_connect(c):
    if c.startswith(ENGINE_CMD_CON):
        return True


async def engine_parse_cmd_scan(c, s, q):
    # s: valid names
    if c.startswith(ENGINE_CMD_SCAN):
        scanner = BleakScanner()
        await scanner.start()
        await asyncio.sleep(4.0)
        await scanner.stop()
        rv = scanner.discovered_devices
        rv = [i.address for i in rv if i.name in s]
        q.put(rv)
        return True


class EngineException(Exception):
    pass
