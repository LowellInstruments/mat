import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import FIRMWARE_VERSION_CMD
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


def gfv():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(FIRMWARE_VERSION_CMD)
            print('\tGFV --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    gfv()
