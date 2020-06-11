import time
import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['mla098']


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
    for _ in range(3):
        gtm_stm()
        print('------')
        time.sleep(1)
    print('APP: done')
