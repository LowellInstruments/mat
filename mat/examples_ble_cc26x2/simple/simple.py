import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


# useful to test any
my_cmd = 'GSR'


def simple():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(my_cmd)
            print('\t\t{} --> {}'.format(my_cmd, rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    simple()
    print('APP: done')
