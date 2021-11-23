from mat.bluepy.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.examples.macs import get_mac


def get_sensor_bat(cla=LoggerControllerBLERN4020):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_bat()
        print('> battery: {} mV'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    get_sensor_bat()
