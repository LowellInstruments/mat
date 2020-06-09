import bluepy.btle as ble
from mat.examples_ble.simple._utils import ensure_stop
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['mla098']


def get_dummy():
    try:
        with LoggerControllerBLE(mac) as lc:

            # stop the logger
            ensure_stop(lc)

            # download
            name = 'dummy.lid'
            size = 40960
            print('\tGetting {}...', name)
            rv = lc.get_file(name, '.', size)
            print(rv)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    get_dummy()

