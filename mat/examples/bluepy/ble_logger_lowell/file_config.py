from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.macs import get_mac


def file_config(c: dict, cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_cfg(c)
        print('> config cmd: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    d = {
        "DFN": "low",
        "TMP": 0, "PRS": 0,
        "DOS": 1, "DOP": 1, "DOT": 1,
        "TRI": 10, "ORI": 10, "DRI": 30,
        "PRR": 1,
        "PRN": 1,
        "STM": "2012-11-12 12:14:00",
        "ETM": "2030-11-12 12:14:20",
        "LED": 1
    }
    file_config(d)
