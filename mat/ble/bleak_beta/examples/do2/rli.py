from mat.ble.ble_macs import MAC_LOGGER_DO2_0_MODBUS
from mat.ble.bleak_beta.logger_do2 import LoggerDO2
from mat.ble.bleak_beta.logger_do2_dummy import LoggerDO2Dummy


def rli(dummy=False):
    mac = MAC_LOGGER_DO2_0_MODBUS
    lc_class = LoggerDO2Dummy if dummy else LoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_rli()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    rli()
