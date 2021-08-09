import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller_ble import LoggerControllerBLE, MOBILE_CMD

mac = mac_ble_cc26x2


def ensure_mbl_mode_on(lc):
    rv = lc.command(MOBILE_CMD)
    print('\tMBL --> {}'.format(rv))
    if rv[1][-1] == 49:
        return
    rv = lc.command(MOBILE_CMD)
    print('\tMBL --> {}'.format(rv))


def mbl():
    try:
        with LoggerControllerBLE(mac) as lc:
            ensure_mbl_mode_on(lc)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    mbl()
