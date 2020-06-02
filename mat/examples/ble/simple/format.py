import bluepy.btle as ble
from mat.logger_controller import (LOGGER_INFO_CMD_W,
                                   LOGGER_INFO_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple._utils import ensure_stop
from mat.examples.ble.simple import _macs

# mac = _macs.puz
mac = _macs.sxt050


def fmt(dri=10):
    try:
        with LoggerControllerBLE(mac) as lc:
            ensure_stop(lc)

            result = lc.sync_time()
            print('\t\tSTM --> {}'.format(result))

            result = lc.get_time()
            print('\t\tGTM --> {}'.format(result))

            result = lc.command('FRM', retries=1)
            print('\t\tFRM --> {}'.format(result))

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
            result = lc.send_cfg(cfg)
            print('\t\tCFG --> {}'.format(result))

            result = lc.command(LOGGER_INFO_CMD_W, "BA8007")
            print('\t\tWLI (BA) --> {}'.format(result))

            result = lc.command(LOGGER_INFO_CMD, "BA")
            print('\t\tRLI (BA) --> {}'.format(result))

            result = lc.command(LOGGER_INFO_CMD_W, "SN1234567")
            print('\t\tWLI (SN) --> {}'.format(result))

            result = lc.command(LOGGER_INFO_CMD, "SN")
            print('\t\tRLI (SN) --> {}'.format(result))

            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    fmt(dri=30)
    print('APP: done')
