import time

import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE, CRC_CMD
from mat.crc import calculate_local_file_crc
from mat.examples.bluepy.ble_cc26x2.dwg import _ensure_rm_prev_file
from mat.examples.bluepy.ble_cc26x2.stp_n_run import stop
from mat.examples.bluepy.ble_cc26x2.wak import ensure_wak_is_on
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


FILE_NAME = '2006673_sxt_20210112_130721.lid'
FILE_SIZE = 2206


def get_dummy(name, size):
    try:
        with LoggerControllerBLE(mac) as lc:
            # download
            print('\tGetting {}...'.format(name))
            rv = lc.get_file(name, '.', size)
            print(rv)

            # check CRC
            if not rv:
                print('don\'t CRC, could not download {}'.format(name))
                return
            _crc_loc = calculate_local_file_crc(name)
            _crc_rem = lc.command(CRC_CMD, name)
            s = '\t_crc_loc {} _crc_rem {}'
            print(s.format(_crc_loc, _crc_rem))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    # run()
    if not ensure_wak_is_on():
        ensure_wak_is_on()
    stop()
    _t = time.perf_counter()
    _name = FILE_NAME
    _size = FILE_SIZE
    _ensure_rm_prev_file(_name)
    get_dummy(_name, _size)
    _ = time.perf_counter() - _t
    print('get took {} milliseconds'.format(_ * 1000))
