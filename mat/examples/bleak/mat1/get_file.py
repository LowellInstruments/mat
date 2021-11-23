import time

from mat.bleak.ble_logger_mat1 import BLELoggerMAT1
from mat.bleak.ble_logger_mat1_dummy import BLELoggerMAT1Dummy
from mat.ble_utils_shared import utils_mat_convert_data
from mat.examples.bleak.mat1.macs import mac


def get_file(dummy=False):
    lc_class = BLELoggerMAT1Dummy if dummy else BLELoggerMAT1
    lc = lc_class()
    lc.ble_connect(mac)

    filename = '2011605_TP_1m_(0).lid'
    size = 326492
    rv = lc.ble_cmd_get(filename)
    data = bytes()
    start = time.perf_counter()
    if rv == b'\n\rGET 00\r\n':
        data = lc.ble_cmd_xmodem(size)
    if data:
        path = '/home/kaz/Downloads/puta.lid'
        if utils_mat_convert_data(data, path, size):
            print('converted OK')
        else:
            print('conversion error')
    else:
        print('xmodem error')

    end = time.perf_counter()
    if data:
        _ = size / (end - start)
        print('speed {} KB/s'.format(_ / 1000))

    lc.ble_disconnect()
    lc.ble_bye()


if __name__ == "__main__":
    get_file()
