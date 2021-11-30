import os
from pathlib import Path
from mat.bluepy.logger_controller_ble_moana import LoggerControllerMoana
from mat.examples.bluepy.ble_logger_moana.macs import MAC_MOANA


mac = MAC_MOANA


def moana_demo(fol):

    print('reaching moana {}...'.format(mac))
    lc = LoggerControllerMoana(mac)
    if not lc.open():
        print('connection error')
        return

    lc.auth()
    rv = lc.file_info()
    print(rv)

    name_csv_moana = rv['FileName']
    print('downloading file {}...'.format(name_csv_moana))
    data = lc.file_get()
    name_bin_local = lc.file_save(data)
    if name_bin_local:
        print('saved as {}'.format(name_bin_local))
        name_csv_local = lc.file_cnv(name_bin_local, fol)
        if name_csv_local:
            print('conversion OK')
            p = '{}/{}'.format(fol, name_csv_local)
            print('renamed files as {}*'.format(p))
        else:
            print('conversion error')

    # we are doing OK
    lc.time_sync()

    # comment next 2 -> repetitive download tests
    # uncomment them -> make the logger record
    if not lc.file_clear():
        print('error file_clear')
    lc.moana_end()

    lc.close()


if __name__ == '__main__':
    files_fol = str(Path.home()) + '/Downloads/moana_demo'
    try:
        os.mkdir(files_fol)
    except OSError as error:
        pass
    moana_demo(files_fol)
