import time
from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.macs import get_mac


def measure_oxygen(cla=LoggerControllerBLELowell):

    mac = get_mac(cla)
    lc = cla(mac)

    if lc.open():
        rv = lc.ble_cmd_gdo()
        print('> DO saturation:  {}.{} mg/l'.format(rv[0][:2], rv[0][2:]))
        print('> DO percentage:  {}.{} %'.format(rv[1][:2], rv[1][2:]))
        print('> DO temperature: {}.{} C'.format(rv[2][:2], rv[2][2:]))
        print('\n')
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    while 1:
        measure_oxygen()
        time.sleep(10)
