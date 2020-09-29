import time
import bluepy.btle as ble
from mat.logger_controller import (LOGGER_INFO_CMD_W,
                                   LOGGER_INFO_CMD,
                                   STOP_CMD,
                                   STATUS_CMD,
                                   RUN_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def, sn_def


# use default MAC or override it
mac = mac_def
sn = sn_def


# resets a logger memory and runs it
def frm_n_run():
    try:
        with LoggerControllerBLE(mac) as lc:

            # sets up logger time, memory, serial number
            rv = lc.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(rv))
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))
            rv = lc.sync_time()
            print('\t\tSTM --> {}'.format(rv))
            rv = lc.get_time()
            print('\t\tGTM --> {}'.format(rv))
            rv = lc.command('FRM')
            print('\t\tFRM --> {}'.format(rv))
            cfg_file = {
                'DFN': 'sxt',
                'TMP': 0, 'PRS': 0,
                'DOS': 1, 'DOP': 1, 'DOT': 1,
                'TRI': 10, 'ORI': 10, 'DRI': 10,
                'PRR': 8,
                'PRN': 4,
                'STM': '2012-11-12 12:14:00',
                'ETM': '2030-11-12 12:14:20',
                'LED': 1
            }
            rv = lc.send_cfg(cfg_file)
            print('\t\tCFG --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD_W, 'BA8007')
            print('\t\tWLI (BA) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD, 'BA')
            print('\t\tRLI (BA) --> {}'.format(rv))
            s = 'SN{}'.format(sn)
            rv = lc.command(LOGGER_INFO_CMD_W, s)
            print('\t\tWLI (SN) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD, 'SN')
            print('\t\tRLI (SN) --> {}'.format(rv))

            # starts the logger
            time.sleep(2)
            rv = lc.command(RUN_CMD)
            print('\t\tRUN --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    frm_n_run()
    print('APP: done')
