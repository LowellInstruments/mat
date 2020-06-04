import bluepy.btle as ble
from mat.logger_controller import HW_TEST_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['lp2']


def hw_test():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(HW_TEST_CMD)
            print('\tHW test: can take a couple minutes...')
            print('\t\t#T1 --> {}'.format(rv))
            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    hw_test()
    print('APP: done')
