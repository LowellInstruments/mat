import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


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
    invalid()
