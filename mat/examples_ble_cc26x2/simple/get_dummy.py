import bluepy.btle as ble

from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def get_dummy():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))

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

