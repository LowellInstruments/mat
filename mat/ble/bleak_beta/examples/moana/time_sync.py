from mat.ble.ble_macs import MAC_MOANA_0051
from mat.ble.bleak_beta.logger_moana import LoggerMoana


def time_sync():
    mac = MAC_MOANA_0051
    lc = LoggerMoana()
    lc.ble_connect(mac)
    lc.ble_cmd_time_sync()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    time_sync()
