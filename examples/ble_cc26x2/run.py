import bluepy.btle as ble
from mat.logger_controller import (RUN_CMD, RWS_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2


mac = mac_ble_cc26x2


def run():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(RUN_CMD)
            print('\t\t{} --> {}'.format(RUN_CMD, rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def run_with_string():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(RWS_CMD, 'lab')
            print('\t\t{} --> {}'.format(RWS_CMD, rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    run()
