import time
import bluepy.btle as ble
import pprint
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


# ext: b'lid' or b'gps_bu_353_s4'
def ls_ext(ext: bytes   ):
    try:
        with LoggerControllerBLE(mac) as lc:
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
    for _ in range(1):
        ls_not_lid()
        time.sleep(.1)
        ls_ext(b'lid')
        time.sleep(.1)
        # ls(b'gps_bu_353_s4')
        # time.sleep(.1)
