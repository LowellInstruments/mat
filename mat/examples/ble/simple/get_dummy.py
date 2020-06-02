import bluepy.btle as ble
from mat.examples.ble.simple._utils import ensure_stop
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple import _macs

# mac = _macs.puz
mac = _macs.sxt050


def get_dummy():
    try:
        with LoggerControllerBLE(mac) as lc:

            # stop the logger
            ensure_stop(lc)

            # download
            name = 'dummy.lid'
            size = 4096
            print('\tGetting {}...', name)
            rv = lc.get_file(name, '.', size)
            print(rv)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    get_dummy()

