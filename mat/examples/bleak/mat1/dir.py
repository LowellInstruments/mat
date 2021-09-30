from mat.ble_logger_mat1 import BLELoggerMAT1
from mat.examples.bleak.mat1.macs import MAC_MAT1_0_DUMMY, MAC_MAT1_0


address = MAC_MAT1_0


def list_files(dummy=False):
    lc = BLELoggerMAT1(dummy)
    mac = MAC_MAT1_0_DUMMY if dummy else address
    lc.ble_connect(mac)
    rv = lc.ble_cmd_dir()
    print('parsed list_files -> {}'.format(rv))
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    list_files()
