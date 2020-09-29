import bluepy.btle as ble
from mat.logger_controller import (LOGGER_INFO_CMD_W,
                                   LOGGER_INFO_CMD, STOP_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def frm(dri=10):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))

            rv = lc.sync_time()
            print('\t\tSTM --> {}'.format(rv))

            rv = lc.get_time()
            print('\t\tGTM --> {}'.format(rv))

            rv = lc.command('FRM')
            print('\t\tFRM --> {}'.format(rv))

            # ex: PRR = 16, PRN = 65535 --> 4095 > SRI = 3600
            cfg_do = {
                            "DFN": "low",
                            "TMP": 0, "PRS": 0,
                            "DOS": 1, "DOP": 1, "DOT": 1,
                            "TRI": 10, "ORI": 10, "DRI": dri,
                            "PRR": 8,
                            "PRN": 4,
                            "STM": "2012-11-12 12:14:00",
                            "ETM": "2030-11-12 12:14:20",
                            "LED": 1
            }
            cfg = cfg_do
            rv = lc.send_cfg(cfg)
            print('\t\tCFG --> {}'.format(rv))

            rv = lc.command(LOGGER_INFO_CMD_W, "BA8007")
            print('\t\tWLI (BA) --> {}'.format(rv))

            rv = lc.command(LOGGER_INFO_CMD, "BA")
            print('\t\tRLI (BA) --> {}'.format(rv))

            rv = lc.command(LOGGER_INFO_CMD_W, "SN1234567")
            print('\t\tWLI (SN) --> {}'.format(rv))

            rv = lc.command(LOGGER_INFO_CMD, "SN")
            print('\t\tRLI (SN) --> {}'.format(rv))

            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    frm(dri=30)
    print('APP: done')
