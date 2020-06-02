import bluepy.btle as ble
from mat.logger_controller import (
    DO_SENSOR_READINGS_CMD,
    SENSOR_READINGS_CMD,
    SD_FREE_SPACE_CMD
)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple._macs import mac


def sense():
    try:
        with LoggerControllerBLE(mac, hci_if=0) as lc_ble:
            result = lc_ble.command(SENSOR_READINGS_CMD, retries=1)
            print('\t\tGSR --> {}'.format(result))

            result = lc_ble.command(DO_SENSOR_READINGS_CMD, retries=1)
            print('\t\tGDO --> {}'.format(result))

            result = lc_ble.command(SD_FREE_SPACE_CMD)
            print('\t\tCFS --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    for _ in range(10):
        sense()
    print('APP: done')
