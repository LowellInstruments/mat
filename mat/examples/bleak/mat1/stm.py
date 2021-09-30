from mat.bleak.ble_logger_mat1 import BLELoggerMAT1
from mat.examples.bleak.mat1.macs import MAC_MAT1_0_DUMMY, MAC_MAT1_0

address = MAC_MAT1_0


def set_time(dummy=False):
    lc = BLELoggerMAT1(dummy)
    mac = MAC_MAT1_0_DUMMY if dummy else address
    lc.ble_connect(mac)
    lc.ble_cmd_stm()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    set_time()
