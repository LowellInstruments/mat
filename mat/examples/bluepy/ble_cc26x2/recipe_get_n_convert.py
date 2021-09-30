import os
import time
from pprint import pprint

import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.crc import calculate_local_file_crc
from mat.data_converter import default_parameters, DataConverter
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override

# global statistics
from mat.utils import PrintColors

dl_attempts = 0
dl_n_cnv_ok = 0
dl_ok = 0
ls_err = 0
conn_err = 0


def print_green(s):
    _PC = PrintColors()
    print('{}{}{}'.format(_PC.OKGREEN, s, _PC.ENDC))


def get_n_convert():
    global dl_ok
    global dl_n_cnv_ok
    global dl_attempts
    global ls_err
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command('STP')
            print('\tSTP --> {}'.format(rv))

            # obtain the list of .lid files
            files = lc.ls_lid()
            print('\tDIR lid -->')
            pprint(files)

            # precaution
            if files == [b'ERR']:
                print('ls() returned ERR')
                ls_err += 1
                time.sleep(20)
                return

            # download and convert such files
            for name, size in files.items():
                dl_attempts += 1
                print('\tGetting file {}...'.format(name))
                rv = lc.get_file(name, '.', size)
                print('\t\tgot {}, size {}'.format(name, size))

                if rv:
                    # checksum check
                    _crc_loc = calculate_local_file_crc(name)
                    _crc_rem = lc.command('CRC', name)
                    s = '\t_crc_loc {} _crc_rem {}'
                    print(s.format(_crc_loc, _crc_rem))
                    if type(_crc_rem) != list or len(_crc_rem) != 2:
                        return

                    # [b'CRC', b'081c8992d4']
                    _ = _crc_rem[1][-8:].decode().upper()
                    if _crc_loc != _:
                        return

                    # CRC is ok
                    dl_ok += 1

                    print('\t\tConverting --> ', end='')
                    try:
                        pars = default_parameters()
                        converter = DataConverter(name, pars)
                        s = time.time()
                        converter.convert()
                        e = time.time()
                        dl_n_cnv_ok += 1
                        print('ok ({}s)'.format(e - s))
                    except Exception as ex:
                        print('error')
                        print(ex)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def _get_n_rm_local_ext_files_list(ext):
    _ = os.listdir('.')
    for item in _:
        if item.endswith(ext):
            print(item)
            os.remove(item)


def main():
    global dl_ok
    global dl_n_cnv_ok
    global dl_attempts
    global conn_err

    ext = 'lid'
    while 1:
        _get_n_rm_local_ext_files_list(ext)
        get_n_convert()
        print_green('dl ok: {} / {}'.format(dl_ok, dl_attempts))
        print_green('dl_n_cnv ok: {} / {}'.format(dl_n_cnv_ok, dl_attempts))
        print_green('ls err: {} conn err {}'.format(ls_err, conn_err))
        time.sleep(5)


if __name__ == '__main__':
    while 1:
        try:
            main()
        except AttributeError:
            conn_err += 1
            # when cannot connect, for example :)
            print('could not connect momentarily')
            time.sleep(5)
