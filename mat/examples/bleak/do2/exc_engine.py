from mat.bleak.ble_logger_do2 import BLELoggerDO2, ExceptionLCDO2
from mat.bleak.ble_logger_do2_utils import ENGINE_CMD_EXC
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY, MAC_DO2_0


address = MAC_DO2_0


def exc_engine(dummy=False):
    lc = BLELoggerDO2(dummy)
    mac = MAC_DO2_0_DUMMY if dummy else address
    lc.ble_connect(mac)

    # we force this to happen
    a = lc.ble_cmd_exc_engine()

    # propagate the exception to higher app layers
    if a == ENGINE_CMD_EXC:
        ex = '(ap) ! (from en) {}, quitting'.format(a)
        raise ExceptionLCDO2(ex)

    # this will NOT take place
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    exc_engine()
