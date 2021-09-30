import os

from bleak import BleakError

from mat.ble_logger_do2 import BLELoggerDO2, ExceptionLCDO2
from mat.ble_logger_do2_utils import ENGINE_CMD_EXC
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY, MAC_DO2_0


address = MAC_DO2_0


def exc_lc(dummy=False):
    lc = BLELoggerDO2(dummy)
    mac = MAC_DO2_0_DUMMY if dummy else address
    lc.ble_connect(mac)

    try:
        lc.ble_cmd_exc_lc()
    except (BleakError, ExceptionLCDO2) as ex:
        print('(ap) ! (from lc) {}, quitting'.format(ex))
        os._exit(1)

    # this will NOT take place
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    exc_lc()
