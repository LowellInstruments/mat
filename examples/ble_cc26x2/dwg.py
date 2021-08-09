import os
import time
import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.crc import calculate_local_file_crc
from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2

FILE_NAME = 'dummy_133.lid'
FILE_SIZE = 167936

g_dl_ok = 0
g_dl_attempts = 0


def _ensure_rm_prev_file(path):
    try:
        os.remove(path)
    except OSError as error:
        pass


def dwg(file_name, file_size):
    global g_dl_ok
    global g_dl_attempts

    try:
        with LoggerControllerBLE(mac) as lc:
            # ensure_mbl_mode_on(lc)

            c = STOP_CMD
            r = lc.command(c)
            print('\t\t{} --> {}'.format(c, r))

            # dwg & dwl
            print('\tDownGING {}...'.format(file_name))
            _ensure_rm_prev_file(file_name)
            data = lc.dwg_file(file_name, '.', file_size)
            if data:
                print('DWG went ok')
                print(data[:4])
                g_dl_ok += 1
            else:
                print('DWG failed somehow')

            g_dl_attempts += 1

            print('percentage ok {} / {}'.format(g_dl_ok, g_dl_attempts))

            # check
            _crc_loc = calculate_local_file_crc(file_name)
            _crc_rem = lc.command('CRC', file_name)
            s = '\t_crc_loc {} _crc_rem {}'
            print(s.format(_crc_loc, _crc_rem))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':

    while 1:
        dwg(FILE_NAME, FILE_SIZE)
        time.sleep(10)
