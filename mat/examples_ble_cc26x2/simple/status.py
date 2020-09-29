import bluepy.btle as ble
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def status():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    for _ in range(2):
        status()
    print('APP: done')
