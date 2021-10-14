from mat.bleak.ble_logger_moana import BLELoggerMoana
from mat.examples.bleak.moana.macs import mac


def auth():
    lc_class = BLELoggerMoana
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_auth()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    auth()
