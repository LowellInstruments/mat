import time

import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from examples.ble_cc26x2.dir import ls_ext
from examples.ble_cc26x2.dwg import _ensure_rm_prev_file
from examples.ble_cc26x2.stp import stop
from mat.crc import calculate_local_file_crc
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble import LoggerControllerBLE, CRC_CMD

mac = mac_ble_cc26x2


FILE_NAME = 'dummy_2559.lid'
FILE_SIZE = 167936


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
    stop()
    ls_ext(b'lid')
    _t = time.perf_counter()
    _name = FILE_NAME
    _size = FILE_SIZE
    _ensure_rm_prev_file(_name)
    get_dummy(_name, _size)
    _ = time.perf_counter() - _t
    print('get took {} milliseconds'.format(_ * 1000))
