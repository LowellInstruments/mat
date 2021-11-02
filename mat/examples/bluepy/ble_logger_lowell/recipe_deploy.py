from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.macs import get_mac


def deploy(c_d: dict, cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_stp()
        print('> stop: {}'.format(rv))
        rv = lc.ble_cmd_frm()
        print('> format: {}'.format(rv))
        rv = lc.ble_cmd_sts()
        print('> status: {}'.format(rv))
        rv = lc.ble_cmd_wli("SN1234567")
        print('> set info SN: {}'.format(rv))
        rv = lc.ble_cmd_wli("CA1234")
        print('> set info CA: {}'.format(rv))
        rv = lc.ble_cmd_wli("BA5678")
        print('> set info BA: {}'.format(rv))
        rv = lc.ble_cmd_wli("MA1234ABC")
        print('> set info MA: {}'.format(rv))
        rv = lc.ble_cmd_cfg(c_d)
        print('> config cmd: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    # todo > re-check this conf is valid
    _cfg_dict = {
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
    deploy(_cfg_dict)
