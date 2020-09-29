import bluepy.btle as ble
from mat.data_converter import DataConverter, default_parameters
from mat.logger_controller_ble import LoggerControllerBLE
import os
from pprint import pprint
import time
import sys
from mat.examples_ble_cc26x2._macs import mac_def, sn_def


# use default MAC or override it
mac = mac_def
sn = sn_def


# stops a logger and download its gps files
def stp_n_dl_gps():
    try:
        with LoggerControllerBLE(mac) as lc:

            # stop the logger
            rv = lc.command('STP')
            print('\tSTP --> {}'.format(rv))

            # obtain the list of .gps files
            files = lc.ls_ext(b'gps')
            print('\tDIR -->')
            pprint(files)

            # precaution
            if files == [b'ERR']:
                print('ls() returned ERR, try again')
                sys.exit(1)

            # download gps files
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
def stp_n_dl_lid():
    try:
        with LoggerControllerBLE(mac) as lc:

            # stop the logger
            rv = lc.command('STP')
            print('\tSTP --> {}'.format(rv))

            # obtain the list of .lid files
            files = lc.ls_ext(b'lid')
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
                print('\tDownloading {}...', name)
                rv = lc.get_file(name, '.', size)
                if rv:
                    print('\t\tgot {}, size {}'.format(name, size))
                    print('\t\tConverting --> ', end='')
                    try:
                        pars = default_parameters()
                        converter = DataConverter(name, pars)
                        s = time.time()
                        converter.convert()
                        e = time.time()
                        print('ok ({}s)'.format(e - s))
                    except Exception as ex:
                        print('error')
                        print(ex)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    stp_n_dl_lid()
    stp_n_dl_gps()
