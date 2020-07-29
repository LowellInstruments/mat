import os
import time
import bluepy.btle as ble
from mat.data_converter import default_parameters, DataConverter
from mat.logger_controller_ble import LoggerControllerBLE
import sys
from pprint import pprint
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['mla098']


# stops a logger and download its data files
def ls_dl_convert():
    try:
        with LoggerControllerBLE(mac) as lc_ble:

            # stop the logger
            rv = lc_ble.command('STP')
            print('\tSTP --> {}'.format(rv))

            # obtain the list of .lid files
            files = lc_ble.ls_ext(b'lid')
            print('\tDIR -->')
            pprint(files)


            # download and convert such files
            for name, size in files.items():
                if os.path.exists(name):
                    print('\t\talready have {}'.format(name))
                    continue
                print('\tDownloading {}...', name)
                rv = lc_ble.get_file(name, '.', size)
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
    ls_dl_convert()
