from mat.ble_logger_do2 import BLELoggerDO2
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY, MAC_DO2_0


address = MAC_DO2_0


def delete_file(file_name, dummy=False):
    lc = BLELoggerDO2(dummy)
    mac = MAC_DO2_0_DUMMY if dummy else address
    lc.ble_connect(mac)
    lc.ble_cmd_del(file_name)
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    delete_file('dummy_750.lid')
