import os
import time
import bluepy.btle as ble

from mat.bluepy.xmodem_rn4020 import ble_xmd_get_file_rn4020
from mat.data_converter import default_parameters, DataConverter
from mat.examples.bluepy.ble_logger_rn4020.file_list import ls_lid_rn4020
from mat.utils import PrintColors as p_c
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
import subprocess as sp
from mat.examples.bluepy.ble_logger_rn4020.macs import MAC_LOGGER_MAT1_0

mac = MAC_LOGGER_MAT1_0

dl_ok = 0
dl_n_cnv_ok = 0
dl_attempts = 0


def _get_n_rm_local_ext_files_list(ext):
    _ = os.listdir('.')
    for item in _:
        if item.endswith(ext):
            os.remove(item)


def _print_green(_s):
    print('{}{}{}'.format(p_c.OKGREEN, _s, p_c.ENDC))


def _print_blue(_s):
    print('{}{}{}'.format(p_c.OKBLUE, _s, p_c.ENDC))


def _print_red(_s):
    print('{}{}{}'.format(p_c.FAIL, _s, p_c.ENDC))


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
        _print_blue('{} = {}'.format(cmd, md5.stdout))
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

    try:
        with LoggerControllerBLE(mac) as lc:
            # set RN4020 fast mode
            _ = lc.send_btc()
            if not _:
                print('\tcould not BTC, leaving')
                return False
            print('\tBTC -> {}'.format(_))

            # GET cmd done by us not command()
            lc.dlg.clr_buf()
            g = 'GET {:02x}{}\r'
            cmd = g.format(len(f_name), f_name)
            lc.ble_write(cmd.encode())
            _till = time.time() + 5
            while 1:
                lc.per.waitForNotifications(.1)
                if time.time() >= _till:
                    _print_red('\terror GET')
                    return False
                _ = lc.dlg.buf.decode().strip()
                if _ == 'GET 00':
                    break

            # XMODEM because GET went well
            s = '\tDownloading {}, {} bytes...'
            print(s.format(f_name, f_size))
            lc.dlg.set_file_mode(True)
            el = time.perf_counter()
            rv, f_data = ble_xmd_get_file_rn4020(lc)
            lc.dlg.set_file_mode(False)
            if rv and len(f_data) >= f_size:
                dl_ok += 1
                el = time.perf_counter() - el
                s = '\t--> data rate {} bytes / sec'
                _print_green(s.format(int(f_size / el)))
                _convert_file(f_data, f_name, f_size)
            else:
                _print_red('error downloading')

    except ble.BTLEException as ble_ex:
        print(ble_ex)

    except AttributeError as ae:
        print(ae)

    finally:
        lc.dlg.set_file_mode(False)


def main():
    global dl_ok
    global dl_n_cnv_ok

    ls_lid_rn4020()
    name, size = '2011605_TP_1m_(0).lid', 326492

    # download repetitions
    n = 1000

    dl_ok = 0
    dl_n_cnv_ok = 0

    for i in range(n):
        _get_n_rm_local_ext_files_list('lid')
        _get_n_rm_local_ext_files_list('csv')
        _get_n_convert(name, size)
        _print_blue('dl_ok {} / {}'.format(dl_ok, i + 1))
        _print_blue('dl_n_cnv_ok {} / {}'.format(dl_n_cnv_ok, i + 1))
        time.sleep(10)


if __name__ == '__main__':
    main()


