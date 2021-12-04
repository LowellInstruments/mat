from mat.ble.ble_macs import MAC_LOGGER_DO2_0_MODBUS
from mat.ble.bleak_beta.logger_do2 import LoggerDO2
from mat.ble.bleak_beta.logger_do2_dummy import LoggerDO2Dummy


cfg = {
    "DFN": "low",
    "TMP": 1, "PRS": 1,
    "DOS": 0, "DOP": 0, "DOT": 0,

    "TRI": 10, "ORI": 10, "DRI": 900,
    "PRR": 1,
    "PRN": 1,

    "STM": "2012-11-12 12:14:00",
    "ETM": "2030-11-12 12:14:20",
    "LED": 1
}


def config(s_as_dict, dummy=False):
    mac = MAC_LOGGER_DO2_0_MODBUS
    lc_class = LoggerDO2Dummy if dummy else LoggerDO2
    lc = lc_class()
    lc.ble_connect(mac)
    lc.ble_cmd_stp()
    lc.ble_cmd_cfg(s_as_dict)
    lc.ble_cmd_mci()
    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    config(cfg)
