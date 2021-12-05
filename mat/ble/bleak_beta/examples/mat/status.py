from mat.ble.ble_macs import MAC_LOGGER_MAT1_0
from mat.ble.bleak_beta.logger_mat import LoggerMAT


def status():
    mac = MAC_LOGGER_MAT1_0
    lc = LoggerMAT()
    lc.ble_connect(mac)
    lc.ble_cmd_sts()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    status()
