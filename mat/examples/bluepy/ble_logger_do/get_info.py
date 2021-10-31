from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12



def example_get_info():
    lc = LoggerControllerBLELowell(mac)
    if lc.open():
        rv = lc.ble_cmd_rli()
        print('> get info : {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    example_get_info()
