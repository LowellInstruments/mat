from mat.bleak.ble_logger_moana import BLELoggerMoana
from mat.examples.bleak.moana.macs import mac


def time_sync():
    lc_class = BLELoggerMoana
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_time_sync()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    time_sync()
