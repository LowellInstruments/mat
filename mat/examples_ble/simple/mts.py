import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['lp2']


def mts():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command('MTS')
            print('\t\tMTS --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    mts()
    print('APP: done')
