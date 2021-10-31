import time
from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12



def example_get_dissolved_oxygen():
    lc = LoggerControllerBLELowell(mac)
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
        example_get_dissolved_oxygen()
        time.sleep(10)
