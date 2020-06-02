import bluepy.btle as ble
from mat.logger_controller import REQ_FILE_NAME_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple import _macs

# mac = _macs.lp2
mac = _macs.sxt050


def rfn():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command(REQ_FILE_NAME_CMD)
            print('\t\tRFN --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')

    rfn()

    print('APP: done')
