from mat.ble.ble_macs import MAC_LOGGER_DO2_0_MODBUS
from mat.ble.bleak_beta.mat1_logger import BLELoggerMAT1


def list_files():
    mac = MAC_LOGGER_DO2_0_MODBUS
    lc = BLELoggerMAT1()
    lc.ble_connect(mac)
    rv = lc.ble_cmd_dir()
    print('\tparsed ls: {}'.format(rv))
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    list_files()
