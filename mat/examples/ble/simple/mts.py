import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple import _macs

# mac = _macs.puz
mac = _macs.sxt050


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
