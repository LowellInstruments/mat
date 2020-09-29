import bluepy.btle as ble
from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def cfg():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))

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
