from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.macs import get_mac


def set_info(cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_wli("SN1234567")
        print('> set info SN: {}'.format(rv))
        rv = lc.ble_cmd_wli("CA1234")
        print('> set info CA: {}'.format(rv))
        rv = lc.ble_cmd_wli("BA5678")
        print('> set info BA: {}'.format(rv))
        rv = lc.ble_cmd_wli("MA1234ABC")
        print('> set info MA: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    set_info()
