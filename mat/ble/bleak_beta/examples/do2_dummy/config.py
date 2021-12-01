from mat.ble.bleak_beta.examples.do2.config import config


cfg = {
    "DFN": "low",
    "TMP": 0, "PRS": 0,
    "DOS": 1, "DOP": 1, "DOT": 1,
    "TRI": 10, "ORI": 10, "DRI": 900,
    "PRR": 8,
    "PRN": 4,
    "STM": "2012-11-12 12:14:00",
    "ETM": "2030-11-12 12:14:20",
    "LED": 1
}


if __name__ == "__main__":
    config(cfg, dummy=True)
