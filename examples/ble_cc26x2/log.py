import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller_ble import LoggerControllerBLE, LOG_EN_CMD

mac = mac_ble_cc26x2


def log_en():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(LOG_EN_CMD)
            print('\tLOG --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    log_en()
