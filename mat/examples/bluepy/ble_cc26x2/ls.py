import pprint
import time

import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.examples.bluepy.ble_cc26x2.stp_n_run import stop
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override

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
        stop()
        ls_not_lid()
        time.sleep(.1)
        ls_ext(b'lid')
        time.sleep(.1)
        # ls(b'gps_bu_353_s4')
        # time.sleep(.1)
