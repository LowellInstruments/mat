from mat.ble.ble_macs import MAC_MOANA_0051
from mat.ble.bleak_beta.ble_logger_do2 import BLELoggerDO2
from mat.ble.bleak_beta.ble_logger_do2_dummy import BLELoggerDO2Dummy


def battery(dummy=False):
    mac = MAC_MOANA_0051
    lc_class = BLELoggerDO2Dummy if dummy else BLELoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_bat()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    battery()
