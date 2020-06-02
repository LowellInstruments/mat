import os
import time
from os import getcwd
from mat.data_converter import default_parameters, DataConverter
from mat.logger_controller_ble import LoggerControllerBLE


def ensure_stop(lc):
    while 1:
        # know previous state
        rv = lc.command('STS')
        print('\tSTS before --> {}'.format(rv))

        # stop before listing files
        rv = lc.command('STP')
        print('\tSTP --> {}'.format(rv))

        # ensure stopped
        rv = lc.command('STS')
        print('\tSTS after --> {}'.format(rv))
        if rv == [b'STS', b'0201']:
            break
        time.sleep(2)


def convert_files(lc: LoggerControllerBLE, files: dict):
    for name, size in files.items():
        if os.path.exists(name):
            print('\t\talready have {}'.format(name))
            continue
        print('\tDownloading {}...', name)
        s_d = time.perf_counter()
        fol = getcwd()
        rv = lc.get_file(name, fol, size)
        e_d = time.perf_counter()
        if rv and name.endswith('.lid'):
            s = '\t\tgot {} ({})B ok, speed {} Bps'
            s = s.format(name, size, size / (e_d - s_d))
            print(s)
            print('\tConverting --> ', end='')
            try:
                parameters = default_parameters()
                converter = DataConverter(name, parameters)
                s_c = time.time()
                converter.convert()
                e_c = time.time()
                print('ok ({}s)'.format(e_c - s_c))
            except Exception as ex:
                print('error')
                print(ex)
