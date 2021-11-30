from mat.ble.bleak_beta.ble_logger_mat1 import BLELoggerMAT1
from mat.ble.bleak_beta.ble_logger_mat1_dummy import BLELoggerMAT1Dummy
from mat.ble.macs import MAC_LOGGER_MAT1_1


mac = MAC_LOGGER_MAT1_1


def status(dummy=False):
    lc_class = BLELoggerMAT1Dummy if dummy else BLELoggerMAT1
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_sts()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    status()
