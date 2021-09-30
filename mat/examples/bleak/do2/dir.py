from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY

address = '60:77:71:22:c8:18'


def list_files(dummy=False):
    lc = BLELoggerDO2(dummy)
    mac = MAC_DO2_0_DUMMY if dummy else address
    lc.ble_connect(mac)
    lc.ble_cmd_dir()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    list_files()
