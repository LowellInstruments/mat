import time
import bluepy.btle as ble
import pprint
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


# ext: b'lid' or b'gps'
def ls(ext):
    try:
        with LoggerControllerBLE(mac) as lc:
            # ensure_stop(lc)
            rv = lc.ls_ext(ext)
            print('\tDIR {} --> '.format(ext))
            pprint.pprint(rv)
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def ls_not_lid():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.ls_not_lid()
            print('\tDIR NOT LID -->')
            pprint.pprint(rv)
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    for _ in range(1):
        ls(b'lid')
        time.sleep(.1)
        # ls(b'gps')
        # time.sleep(.1)
        # ls_not_lid()
        # time.sleep(.1)

    print('APP: done')
