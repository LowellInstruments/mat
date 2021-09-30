import pprint
import time

import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD, STATUS_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


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
    dir_n_sts(b'lid')
