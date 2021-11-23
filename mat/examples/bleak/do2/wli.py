from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.examples.bleak.do2.macs import mac


def wli(data, dummy=False):
    lc_class = BLELoggerDO2Dummy if dummy else BLELoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_wli(data)
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    wli('SN7777777')
