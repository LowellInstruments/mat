import platform
import sys
import time
import subprocess as sp


BLE_LINUX_SYS_PATH = '/sys/kernel/debug/bluetooth/hci{}/'


def ble_scan_bluepy_unordered(hci_if: int, my_to=3.0):    # pragma: no cover
    # hci_if: hciX interface number
    print('scanning via bluepy...')
    try:
        import bluepy
        s = bluepy.btle.Scanner(iface=hci_if)
        # it'd seem external Bluetooth dongles need passive
        _p = True if hci_if else False
        return s.scan(timeout=my_to, passive=_p)

    except OverflowError:
        e = 'SYS: overflow on BLE scan, maybe date time error'
        print(e)
        sys.exit(1)


def ble_scan_bluepy(hci_if: int, my_to=3.0) -> dict:
    # sort scan results by RSSI: reverse=True, farther ones first
    sr = ble_scan_bluepy_unordered(hci_if, my_to=my_to)
    sr = sorted(sr, key=lambda x: x.rssi, reverse=False)
    rv = {}
    for each in sr:
        rv[each.addr] = each.rssi
    return rv


def ble_linux_hard_reset():
    if not platform.system() == 'Linux':
        print('not linux platform to reset')
        return 'OK'
    # hard bluetooth reset
    cmd = 'systemctl stop bluetooth'
    _ = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    rv = _.returncode
    time.sleep(3)
    cmd = 'systemctl start bluetooth'
    _ = sp.run(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    rv += _.returncode
    return 'OK' if rv == 0 else 'error'


def ble_linux_write_parameters(mi, ma, la, h=0):   # pragma: no cover
    """
    try to use these parameters once opened BLE connection
    """

    h = int(h)
    min_ci = BLE_LINUX_SYS_PATH.format(h) + 'conn_min_interval'
    max_ci = BLE_LINUX_SYS_PATH.format(h) + 'conn_max_interval'
    latency = BLE_LINUX_SYS_PATH.format(h) + 'conn_latency'

    def _ble_linux_check_parameters():
        with open(min_ci, 'r') as _:
            assert mi == int(_.readline().rstrip('\n'))
        with open(max_ci, 'r') as _:
            assert ma == int(_.readline().rstrip('\n'))
        with open(latency, 'r') as _:
            assert la == int(_.readline().rstrip('\n'))
        print('BLE linux parameters: {} / {} / {}'.format(mi, ma, la))

    # try to set them, check we could do it
    try:
        c = 'echo {} > {}'.format(ma, max_ci)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(mi, min_ci)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(la, latency)
        sp.run(c, shell=True, check=True)
    except sp.CalledProcessError:
        pass
    try:
        # order is important
        c = 'echo {} > {}'.format(mi, min_ci)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(ma, max_ci)
        sp.run(c, shell=True, check=True)
        c = 'echo {} > {}'.format(la, latency)
        sp.run(c, shell=True, check=True)
    except sp.CalledProcessError:
        pass

    _ble_linux_check_parameters()
    return True


def ble_linux_write_parameters_as_fast(h=0):
    return ble_linux_write_parameters(6, 11, 0, h=h)


# allows simplest code bleak ever
def ble_connect_n_cmd(my_lc_class, mac, cmd_s, *args):
    """
    :param my_lc_class: ex -> LoggerControllerBLEDO
    :param mac: MAC adress
    :param cmd_s: 'ble_cmd_status'
    :param args: parameters of cmd_s
    :return:
    """
    lc = my_lc_class(mac).open()
    cmd = getattr(lc, cmd_s)
    rv = cmd(*args)
    lc.close()
    print('> {} -> {}'.format(cmd_s, rv))


if __name__ == '__main__':
    print(ble_scan_bluepy(0))
