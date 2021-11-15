from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.macs import get_mac


def run(cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_run()
        print('> run: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    run()
