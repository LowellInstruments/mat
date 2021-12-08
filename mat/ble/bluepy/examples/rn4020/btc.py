from mat.ble.bluepy.examples.examples_utils import get_mac
from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020


def btc():
    cla = LoggerControllerRN4020
    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_btc()
        print('btc enabled: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    btc()
