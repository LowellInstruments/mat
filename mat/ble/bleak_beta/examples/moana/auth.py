from mat.ble.ble_macs import MAC_MOANA_0051
from mat.ble.bleak_beta.ble_logger_moana import BLELoggerMoana


def auth():
    mac = MAC_MOANA_0051
    lc_class = BLELoggerMoana
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_auth()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    auth()
