from mat.bleak.ble_logger_mat1 import BLELoggerMAT1
from mat.bleak.ble_logger_mat1_dummy import BLELoggerMAT1Dummy
from mat.examples.bleak.mat1.macs import mac


def list_files(dummy=False):
    lc_class = BLELoggerMAT1Dummy if dummy else BLELoggerMAT1
    lc = lc_class()
    lc.ble_connect(mac)
    rv = lc.ble_cmd_dir()
    print('\tparsed ls: {}'.format(rv))
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    list_files()
