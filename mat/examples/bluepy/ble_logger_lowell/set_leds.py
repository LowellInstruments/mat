from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.macs import get_mac


def blink(cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_led()
        print('> LED: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    blink()
