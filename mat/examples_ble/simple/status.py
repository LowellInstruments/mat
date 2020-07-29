import bluepy.btle as ble
from mat.logger_controller import (STATUS_CMD,
                                   RUN_CMD, STOP_CMD, RWS_CMD, SWS_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs


# used in these examples
mac = _macs['mla071']


def status():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    for _ in range(2):
        status()
    print('APP: done')
