import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple import _macs

# mac = _macs.lp2
mac = _macs.sxt050


def invalid():
    """
    test the logger returns INV on unknown command
    :return: None
    """
    try:
        with LoggerControllerBLE(mac, hci_if=0) as lc_ble:
            result = lc_ble.command('XXX')
            print('\t\tXXX --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    invalid()
    print('APP: done')
