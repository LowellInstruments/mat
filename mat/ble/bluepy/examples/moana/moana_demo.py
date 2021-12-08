import os
import time
from pathlib import Path
from mat.ble.bluepy.examples.moana.macs import MAC_MOANA
from mat.ble.bluepy.moana_logger_controller import LoggerControllerMoana


mac = MAC_MOANA


def just_delete_file_n_time_sync():
    print('reaching moana to time sync {}...'.format(mac))
    lc = LoggerControllerMoana(mac)
    if not lc.open():
        print('connection error')
        return

    lc.auth()
    if not lc.time_sync():
        print('error time sync')
    if not lc.file_clear():
        print('error file_clear')
    lc.close()


def full_demo(fol):
    print('reaching moana {}...'.format(mac))
    lc = LoggerControllerMoana(mac)
    if not lc.open():
        print('connection error')
        return

    lc.auth()
    rv = lc.file_info()

    name_csv_moana = rv['FileName']
    print('downloading file {}...'.format(name_csv_moana))
    data = lc.file_get()

    name_bin_local = lc.file_save(data)
    if name_bin_local:
        print('saved as {}'.format(name_bin_local))

        name_csv_local = lc.file_cnv(name_bin_local, fol, len(data))

        if name_csv_local:
            print('conversion OK')
            p = '{}/{}'.format(fol, name_csv_local)
            print('output files -> {}*'.format(p))
        else:
            print('conversion error')

    # we are doing OK
    lc.time_sync()

    # comment next 2 -> repetitive download tests
    # uncomment them -> re-run logger
    time.sleep(1)
    if not lc.file_clear():
        print('error file_clear')

    lc.close()


if __name__ == '__main__':
    files_fol = str(Path.home()) + '/Downloads/moana_demo'
    try:
        os.mkdir(files_fol)
    except OSError as error:
        pass

    full_demo(files_fol)

    # just_delete_file_n_time_sync()
