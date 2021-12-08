import time
import bluepy.btle as ble

from mat.ble.bluepy.examples.examples_utils import get_mac
from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
from mat.data_converter import default_parameters, DataConverter
from mat.ble.bluepy.examples.cc26x2r.file_list import file_list
from mat.utils import PrintColors as PC
import subprocess as sp


dl_ok = 0
dl_n_cnv_ok = 0
dl_attempts = 0


def _g(_s):
    print('{}{}{}'.format(PC.OKGREEN, _s, PC.ENDC))


def _b(_s):
    print('{}{}{}'.format(PC.OKBLUE, _s, PC.ENDC))


def _r(_s):
    print('{}{}{}'.format(PC.FAIL, _s, PC.ENDC))


def _convert_file(data, path, _size):
    global dl_n_cnv_ok
    if data == b'':
        return False
    try:
        with open(path, 'wb') as f:
            f.write(data)
            f.truncate(_size)
        cmd = 'md5sum \'{}\''.format(path)
        md5 = sp.run(cmd, shell=True, stdout=sp.PIPE)
        _b('{} = {}'.format(cmd, md5.stdout))
        pars = default_parameters()
        converter = DataConverter(path, pars)
        converter.convert()
        print('converted {} ok'.format(path))
        dl_n_cnv_ok += 1
        return True

    except Exception as ex:
        print(ex)
        return False


def _get_n_convert(f_name, f_size):
    global dl_ok
    global dl_attempts

    mac = get_mac(LoggerControllerRN4020)
    lc = LoggerControllerRN4020(mac)

    try:
        with lc:
            # set RN4020 fast mode
            if not lc.ble_cmd_btc():
                print('\tcould not BTC, leaving')
                return False

            print('getting {}, {} bytes'.format(f_name, f_size))
            el = time.perf_counter()
            f_data = lc.ble_cmd_get(f_name, f_size)
            if f_data:
                dl_ok += 1
                el = time.perf_counter() - el
                s = 'data rate {} bytes / sec'
                _g(s.format(int(f_size / el)))
                _convert_file(f_data, f_name, f_size)
            else:
                _r('error downloading')

    except ble.BTLEException as ble_ex:
        print(ble_ex)

    except AttributeError as ae:
        print(ae)


def main():
    global dl_ok
    global dl_n_cnv_ok
    dl_ok = 0
    dl_n_cnv_ok = 0

    file_list(cla=LoggerControllerRN4020)
    name, size = '2110407_T&P_(0).lid', 33048

    n = 1
    for i in range(n):
        _get_n_convert(name, size)
        _b('dl_ok {} / {}'.format(dl_ok, i + 1))
        _b('dl_n_cnv_ok {} / {}'.format(dl_n_cnv_ok, i + 1))
        time.sleep(10)


if __name__ == '__main__':
    main()
