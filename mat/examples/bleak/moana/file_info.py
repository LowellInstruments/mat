from mat.bleak.ble_logger_moana import BLELoggerMoana
from mat.examples.bleak.moana.macs import mac


def file_info():
    lc_class = BLELoggerMoana
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_file_info()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    file_info()
