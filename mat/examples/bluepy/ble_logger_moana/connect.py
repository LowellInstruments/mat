import json
from mat.bluepy.logger_controller_ble_moana import LoggerControllerMoana
from mat.examples.bluepy.ble_logger_moana.macs import MAC_MOANA
import time


mac = MAC_MOANA


# basically, leave enough sleep between errors, if any
def moana_test():
    lc = LoggerControllerMoana(mac)

    # connection stage
    # ----------------
    if not lc.open():
        print('\nconnection error')
        return
    print('\nconnected OK to {}'.format(mac))

    rv = lc.auth()
    print(rv)

    rv = lc.time_sync()
    print(rv)

    rv = lc.file_info()
    print(rv)

    data = lc.file_get()

    name = lc.file_save(data)

    rv = lc.file_cnv(name)
    print('conversion {}'.format(rv))

    # not doing next 2 allows repetitive download tests
    # todo > cmd 'archive-> delete data file from sensor
    # todo > cmd 'disconnect' -> makes stop Adv

    lc.close()


if __name__ == '__main__':
    for i in range(1):
        try:
            moana_test()
        except json.decoder.JSONDecodeError:
            # happens when logger is slow to answer
            print('bad moana_test')
            time.sleep(5)
        finally:
            time.sleep(5)

