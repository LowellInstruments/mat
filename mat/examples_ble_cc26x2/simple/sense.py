import bluepy.btle as ble
from mat.logger_controller import (
    DO_SENSOR_READINGS_CMD,
    SENSOR_READINGS_CMD,
    SD_FREE_SPACE_CMD
)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def sense():
    try:
        with LoggerControllerBLE(mac, hci_if=0) as lc:
            rv = lc.command(SENSOR_READINGS_CMD)
            print('\t\tGSR --> {}'.format(rv))

            rv = lc.command(DO_SENSOR_READINGS_CMD)
            print('\t\tGDO --> {}'.format(rv))

            rv = lc.command(SD_FREE_SPACE_CMD)
            print('\t\tCFS --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    for _ in range(1):
        sense()
    print('APP: done')
