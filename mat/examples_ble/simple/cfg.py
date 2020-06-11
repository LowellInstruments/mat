import bluepy.btle as ble
from mat.logger_controller import (LOGGER_INFO_CMD_W,
                                   LOGGER_INFO_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble.simple._utils import ensure_stop
from mat.examples_ble._macs import _macs
import json


# used in these examples
mac = _macs['mla098']


def cfg():
    try:
        with LoggerControllerBLE(mac) as lc:
            ensure_stop(lc)

            # ex: PRR = 16, PRN = 65535 --> 4095 > SRI = 3600
            _cfg = {
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
            result = lc.send_cfg(_cfg)
            print('\t\tCFG --> {}'.format(result))

            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    cfg()
    print('APP: done')
