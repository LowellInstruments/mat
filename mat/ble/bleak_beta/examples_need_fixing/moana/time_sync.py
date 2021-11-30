from mat.ble.bleak_beta.ble_logger_moana import BLELoggerMoana
from mat.ble.macs import MAC_MOANA_0051


def time_sync():
    mac = MAC_MOANA_0051
    lc_class = BLELoggerMoana
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_time_sync()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    time_sync()
