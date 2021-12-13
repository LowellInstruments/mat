from mat.ble.ble_macs import MAC_MOANA_0051
from mat.ble.bleak_beta.logger_moana import LoggerMoana


def file_info():
    mac = MAC_MOANA_0051
    lc = LoggerMoana()
    lc.ble_connect(mac)
    lc.ble_cmd_file_info()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    file_info()
