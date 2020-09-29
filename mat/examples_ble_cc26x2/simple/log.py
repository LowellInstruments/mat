import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE, LOG_EN_CMD
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def log_en():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(LOG_EN_CMD)
            print('\tLOG --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    log_en()
    print('APP: done')
