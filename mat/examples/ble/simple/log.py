import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE, LOG_EN_CMD
from mat.examples.ble.simple import _macs

# mac = _macs.puz
mac = _macs.sxt050


def log_en():
    try:
        with LoggerControllerBLE(mac) as lc_ble:

            result = lc_ble.command(LOG_EN_CMD)
            print('\tLOG --> {}'.format(result))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    log_en()
    print('APP: done')
