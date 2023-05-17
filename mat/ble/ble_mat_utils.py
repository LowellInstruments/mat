import os

import asyncio
import glob
import socket
import subprocess as sp
import time

from mat.crc import calculate_local_file_crc
from mat.utils import linux_is_rpi


DDH_GUI_UDP_PORT = 12349
STATE_DDS_BLE_DOWNLOAD_PROGRESS = 'state_dds_ble_download_progress'
ael = asyncio.get_event_loop()


def ble_mat_lowell_build_cmd(*args):

    # phone commands use aggregated, a.k.a. transparent, mode
    # they do NOT follow LI proprietary format (DWG NNABCD...)
    tp_mode = len(str(args[0]).split(' ')) > 1
    cmd = str(args[0])
    if tp_mode:
        to_send = cmd
    else:
        # build LI proprietary command format
        cmd = str(args[0])
        arg = str(args[1]) if len(args) == 2 else ''
        n = '{:02x}'.format(len(arg)) if arg else ''
        to_send = cmd + ' ' + n + arg
    to_send += chr(13)

    # debug
    # print(to_send.encode())

    # know command tag, ex: 'STP'
    tag = cmd[:3]
    return to_send, tag


def ble_mat_crc_local_vs_remote(path, remote_crc):
    """ calculates local file name CRC and compares to parameter """

    # remote_crc: logger, crc: local
    crc = calculate_local_file_crc(path)
    crc = crc.lower()
    return crc == remote_crc, crc


def _hci_is_up(i: int) -> bool:
    s = 'hciconfig | grep hci{}'.format(i)
    rv = sp.run(s, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode:
        # not even in the list of hci interfaces
        return False
    s = 'hciconfig hci{} | grep RUNNING'.format(i)
    rv = sp.run(s, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    return True if rv.returncode == 0 else False


def _hci_rpi_is_external(i: int) -> bool:
    # USB we use: EDUP brand, Realtek-based, ex. MAC: E8:4E:06:88:D1:8D
    # raspberry pi3 and pi4 has internal BLE == Manufacturer Cypress
    s = 'hciconfig -a hci{} | grep Cypress'.format(i)
    rv = sp.run(s, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    if i == 0 and rv.returncode:
        print('[ MAT ] hci0 but external, be careful for inconsistencies')

    if rv.returncode == 0:
        # Cypress detected, so False
        return False
    # positive value == NOT Cypress == NOT internal == external
    return True


def ble_mat_get_antenna_type():
    n = len(glob.glob('/sys/class/bluetooth/hci*'))

    # not raspberry, different rules apply, just best guess
    if not linux_is_rpi():
        if n == 1:
            return 0, 'internal'
        if _hci_is_up(1):
            return 1, 'external'
        return 0, 'internal'

    # raspberry, when only 1, return whatever we have
    if n == 1:
        rv = 'external' if _hci_rpi_is_external(0) else 'internal'
        return 0, rv

    # more than one, prefer external
    if _hci_rpi_is_external(0):
        if _hci_is_up(0):
            return 0, 'external'
        return 1, 'internal'

    if _hci_rpi_is_external(1):
        if _hci_is_up(1):
            return 1, 'external'
        return 0, 'internal'

    # fallback
    return 0, 'internal'


def ble_mat_progress_dl(data_len, size, ip='127.0.0.1', port=DDH_GUI_UDP_PORT):
    _ = int(data_len) / int(size) * 100 if size else 0
    _ = _ if _ < 100 else 100
    _sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print('{} %'.format(int(_)))
    _ = '{}/{}'.format(STATE_DDS_BLE_DOWNLOAD_PROGRESS, _)

    # always send to localhost
    if ip:
        _sk.sendto(str(_).encode(), (ip, port))

    if ip == '127.0.0.1':
        return

    # only maybe somewhere else :)
    # _sk.sendto(str(_).encode(), (ip, port))


def ble_mat_hci_exists(h):
    if os.getenv("GITHUB_ACTIONS"):
        return
    assert h.startswith('hci')
    assert _hci_is_up(int(h[3]))


def ble_mat_bluetoothctl_power_cycle():
    if not linux_is_rpi():
        print('do not power cycle Bluetooth on non-rpi')
        return
    c = 'bluetoothctl power off'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode:
        print('error powercycle bluetooth off')
    time.sleep(1)
    c = 'bluetoothctl power on'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode:
        print('error powercycle bluetooth on')


async def ble_rfkill_wlan(s):
    if not linux_is_rpi():
        return
    assert s in ('block', 'unblock')
    cmd = 'rfkill {} wlan'.format(s)
    rv = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    await asyncio.sleep(.1)
    if rv.returncode:
        print('** RFKill returned {} -> {}'.format(rv.returncode, rv.stderr))
    return rv
