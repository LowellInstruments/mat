import os
import sys
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
dl_attempts = 0
dl_end = 0
dl_ok = 0


# stops a logger and download its gps_bu_353_s4 files
def stp_n_dl_gps():
    try:
        with LoggerControllerBLE(mac) as lc:

            # stop the logger
            rv = lc.command('STP')
            print('\tSTP --> {}'.format(rv))

            # obtain the list of .gps_bu_353_s4 files
            files = lc.ls_ext(b'gps_bu_353_s4')
            print('\tDIR -->')
            pprint(files)

            # precaution
            if files == [b'ERR']:
                print('ls() returned ERR, try again')
                sys.exit(1)

            # download gps_bu_353_s4 files
            for name, size in files.items():
                if os.path.exists(name):
                    print('\t\talready have {}'.format(name))
                    continue
                print('\tDownloading {}...', name)
                rv = lc.get_file(name, '.', size)
                if rv:
                    print('\t\tgot {}, size {}'.format(name, size))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


# stops a logger and download its data files
def stp_n_dl_ext(ext: str):
    global dl_ok
    global dl_end
    global dl_attempts
    try:
        with LoggerControllerBLE(mac) as lc:

            # stop the logger
            rv = lc.command('STP')
            print('\tSTP --> {}'.format(rv))

            # obtain the list of .lid files
            files = lc.ls_ext(ext.encode())
            print('\tDIR -->')
            pprint(files)

            # precaution
            if files == [b'ERR']:
                print('ls() returned ERR, try again')
                sys.exit(1)

            # download and convert such files
            for name, size in files.items():
                if os.path.exists(name):
                    print('\t\talready have {}'.format(name))
                    continue

                dl_attempts += 1
                print('\tDownloading {}...', name)
                rv = lc.get_file(name, '.', size)
                dl_end += 1
                print('\t\tgot {}, size {}'.format(name, size))

                if rv:
                    # added checksum check
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

                    print('\t\tConverting --> ', end='')
                    try:
                        pars = default_parameters()
                        converter = DataConverter(name, pars)
                        s = time.time()
                        converter.convert()
                        e = time.time()
                        dl_ok += 1
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
    global dl_end
    global dl_attempts

    ext = 'lid'
    while 1:
        _get_n_rm_local_ext_files_list(ext)
        stp_n_dl_ext(ext)
        print('dl ended: {} / {}'.format(dl_end, dl_attempts))
        print('dl ok: {} / {}'.format(dl_ok, dl_attempts))

    # stp_n_dl_gps()


if __name__ == '__main__':
    main()
