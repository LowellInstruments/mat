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

    if rv.returncode == 0:
        # zero == Cypress detected == internal == False
        return False

    # positive == NOT Cypress == NOT internal == external
    return True


def ble_mat_get_antenna_type_v2():
    d = {}
    for i in range(2):
        c = f'hciconfig -a hci{i} | grep Manufacturer'
        rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
        if rv.returncode == 0:
            if b'Cypress' in rv.stdout or b'Intel' in rv.stdout:
                d['internal'] = i
            else:
                d['external'] = i
    # prefer external
    s = 'external' if 'external' in d.keys() else 'internal'
    try:
        return d[s], s
    except (Exception, ) as ex:
        print(f'error: ble_mat_get_antenna_type_v2() -> {ex}')


def ble_mat_get_antenna_type():
    # only kept for old yellow boat DDH version
    return ble_mat_get_antenna_type_v2()


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
    # this is too wild
    # assert _hci_is_up(int(h[3]))


def ble_mat_detect_devices_left_connected_ll():

    # on bad bluetooth state, this takes a long time
    c = 'timeout 2 bluetoothctl info | grep "Connected: yes"'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    if rv.returncode == 124:
        print(f'error: ble_mat_detect_devices_left_connected_ll timeouted')

    if rv.returncode == 1:
        # no devices found connected
        return 0

    c = 'bluetoothctl info'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)

    for lg_type in ('DO-1', 'DO-2', 'TAP1', 'TDO', 'DO1', 'DO2'):
        b = '\tName: {}'.format(lg_type).encode()
        if b in rv.stdout:
            print('ble_mat_detect_devices_left_connected_ll: some connected')
            return 1

    return 0


def ble_mat_systemctl_restart_bluetooth():
    # see stackexchange 758436, this also powers off adapter
    if not linux_is_rpi():
        return
    c = 'sudo systemctl restart bluetooth'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    if rv.returncode:
        print(f'error: ble_mat_systemctl_restart_bluetooth {rv.stderr}')


def ble_mat_get_bluez_version() -> str:
    c = 'bluetoothctl -v'
    rv = sp.run(c, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    v = rv.stdout.decode()
    # v: b'bluetoothctl: 5.55\n'
    v = v.replace('\n', '').split(': ')[1]
    print('MAT: bluez version is', v)
    return str(v)


def ble_mat_bluetoothctl_power_cycle():
    # we don't do this anymore
    pass
