from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.examples.bleak.do2.macs import mac
from mat.bleak.ble_logger_do2_dummy import BLELoggerDO2Dummy


def set_time(dummy=False):
    lc_class = BLELoggerDO2Dummy if dummy else BLELoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_stm()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    set_time()
