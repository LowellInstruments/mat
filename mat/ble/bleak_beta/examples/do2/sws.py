from mat.ble.ble_macs import MAC_LOGGER_DO2_0_MODBUS
from mat.ble.bleak_beta.ble_logger_do2 import BLELoggerDO2
from mat.ble.bleak_beta.ble_logger_do2_dummy import BLELoggerDO2Dummy


def sws(file_name, dummy=False):
    mac = MAC_LOGGER_DO2_0_MODBUS
    lc_class = BLELoggerDO2Dummy if dummy else BLELoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_sws(file_name)
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    sws('stop_at_lab')
