import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def invalid():
    """
    test the logger returns INV on unknown command
    :return: None
    """
    try:
        with LoggerControllerBLE(mac, hci_if=0) as lc:
            result = lc.command('XXX')
            print('\t\tXXX --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    invalid()
    print('APP: done')
