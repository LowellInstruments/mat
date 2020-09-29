import time
import bluepy.btle as ble
import pprint
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def dir_n_sts(ext):
    try:
        with LoggerControllerBLE(mac) as lc:
            for _ in range(10):
                rv = lc.command(STATUS_CMD)
                print('\t\tSTS --> {}'.format(rv))
                rv = lc.ls_ext(ext)
                print('\tDIR {} --> '.format(ext))
                pprint.pprint(rv)
                time.sleep(.1)
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    dir_n_sts(b'lid')
    print('APP: done')
