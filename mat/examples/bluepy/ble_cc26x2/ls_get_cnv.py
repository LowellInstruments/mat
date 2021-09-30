import os
import time
from pprint import pprint

import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.data_converter import default_parameters, DataConverter
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


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
