import os
from pathlib import Path
from mat.bluepy.logger_controller_ble_moana import LoggerControllerMoana
from mat.examples.bluepy.ble_logger_moana.macs import MAC_MOANA


mac = MAC_MOANA


def moana_demo(fol):

    lc = LoggerControllerMoana(mac)
    if not lc.open():
        print('\nconnection error')
        return
    print('\nconnected OK to {}'.format(mac))

    lc.auth()
    lc.time_sync()
    lc.file_info()

    print('downloading file...')
    data = lc.file_get()
    name = lc.file_save(data)
    if name:
        print('saved to {}'.format(name))
        lc.file_cnv(name, fol)
        print('converted')

    # omit next 2 for repetitive download tests
    # todo > cmd 'archive-> delete data file from sensor
    # todo > cmd 'disconnect' -> makes stop Adv

    lc.close()


if __name__ == '__main__':
    files_fol = str(Path.home()) + '/Downloads/moana_demo'
    try:
        os.mkdir(files_fol)
    except OSError as error:
        pass
    moana_demo(files_fol)
