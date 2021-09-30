from mat.bleak.ble_logger_do2 import BLELoggerDO2
from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY, MAC_DO2_0


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


address = MAC_DO2_0


def config(s_as_dict, dummy=False):
    lc = BLELoggerDO2(dummy)
    mac = MAC_DO2_0_DUMMY if dummy else address
    lc.ble_connect(mac)
    lc.ble_cmd_stp()
    # lc.ble_cmd_cfg(s_as_dict)
    # lc.ble_cmd_mci()
    lc.ble_cmd_run()
    # lc.ble_disconnect()
    # lc.ble_bye()


if __name__ == "__main__":
    config(cfg)
