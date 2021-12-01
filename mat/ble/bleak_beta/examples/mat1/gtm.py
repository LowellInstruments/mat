from mat.ble.ble_macs import MAC_LOGGER_MAT1_0
from mat.ble.bleak_beta.mat1_logger import BLELoggerMAT1
from mat.ble.bleak_beta.mat1_logger_dummy import BLELoggerMAT1Dummy


def gtm(dummy=False):
    mac = MAC_LOGGER_MAT1_0
    lc_class = BLELoggerMAT1Dummy if dummy else BLELoggerMAT1
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_gtm()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    gtm()
