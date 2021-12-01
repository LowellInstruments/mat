from mat.ble.ble_macs import MAC_LOGGER_DO2_0_MODBUS
from mat.ble.bleak_beta.mat1_logger import BLELoggerMAT1
from mat.ble.bleak_beta.mat1_logger_dummy import BLELoggerMAT1Dummy


def list_files(dummy=False):
    mac = MAC_LOGGER_DO2_0_MODBUS
    lc_class = BLELoggerMAT1Dummy if dummy else BLELoggerMAT1
    lc = lc_class()
    lc.ble_connect(mac)
    rv = lc.ble_cmd_dir()
    print('\tparsed ls: {}'.format(rv))
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    list_files()
