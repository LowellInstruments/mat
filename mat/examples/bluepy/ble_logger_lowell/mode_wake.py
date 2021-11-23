from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.macs import get_mac


def toggle_mode_wake(cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_wak()
        print('> wake mode enabled: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    toggle_mode_wake()
