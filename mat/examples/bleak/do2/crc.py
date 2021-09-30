from mat.examples.bleak.do2.macs import MAC_DO2_0
from mat.bleak.ble_logger_do2 import BLELoggerDO2


mac = MAC_DO2_0


if __name__ == "__main__":

    lc = BLELoggerDO2()
    lc.ble_connect(mac)
    # DIR before so you know a valid filename
    filename = 'dummy_73286.lid'
    lc.ble_cmd_crc(filename)
    lc.ble_disconnect()
    lc.ble_bye()
