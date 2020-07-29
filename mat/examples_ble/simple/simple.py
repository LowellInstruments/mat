import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs


# used in these examples
mac = _macs['mla098']

# useful to test a command that changes
my_cmd = 'UTM'


def simple():
    try:
        with LoggerControllerBLE(mac) as lc:
            result = lc.command(my_cmd)
            print('\t\t{} --> {}'.format(my_cmd, result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    simple()
    print('APP: done')
