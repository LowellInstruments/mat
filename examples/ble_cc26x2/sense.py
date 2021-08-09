import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import SENSOR_READINGS_CMD, DO_SENSOR_READINGS_CMD, SD_FREE_SPACE_CMD
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


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
    for _ in range(1):
        sense()
