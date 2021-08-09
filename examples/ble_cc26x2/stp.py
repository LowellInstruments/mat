import bluepy.btle as ble
from mat.logger_controller import (STOP_CMD, SWS_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2


mac = mac_ble_cc26x2


def stop():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(STOP_CMD)
            print('\t\t{} --> {}'.format(STOP_CMD, rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def stop_with_string():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(SWS_CMD, 'lab')
            print('\t\t{} --> {}'.format(SWS_CMD, rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    stop()
