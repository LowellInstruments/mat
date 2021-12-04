from mat.ble.ble_macs import MAC_LOGGER_DO2_0_MODBUS
from mat.ble.bleak_beta.logger_do2_dummy import LoggerDO2Dummy
from mat.ble.bleak_beta.logger_do2 import LoggerDO2


def crc(dummy=False):
    mac = MAC_LOGGER_DO2_0_MODBUS
    lc_class = LoggerDO2Dummy if dummy else LoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    # DIR before so you know a valid filename
    filename = 'dummy_73286.lid'
    lc.ble_cmd_crc(filename)
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    crc()
