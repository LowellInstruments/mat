from mat.ble.bleak_beta.ble_logger_do2 import BLELoggerDO2
from mat.ble.bleak_beta.examples_need_fixing import mac
from mat.ble.bleak_beta.ble_logger_do2_dummy import BLELoggerDO2Dummy


def create_fake_file(dummy=False):
    lc_class = BLELoggerDO2Dummy if dummy else BLELoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_mts()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    create_fake_file()
