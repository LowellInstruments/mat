import time

import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple import _macs

# mac = _macs.puz
mac = _macs.sxt050


def gtm_stm():
    try:
        with LoggerControllerBLE(mac) as lc_ble:

            result = lc_ble.command('STP')
            print('\tSTP --> {}'.format(result))

            rv = lc_ble.get_time()
            print('\tGTM --> {}'.format(rv))

            rv = lc_ble.sync_time()
            print('\tSTM --> {}'.format(rv))

            rv = lc_ble.get_time()
            print('\tGTM --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    for _ in range(1):
        gtm_stm()
        print('------')
        time.sleep(3)
    print('APP: done')
