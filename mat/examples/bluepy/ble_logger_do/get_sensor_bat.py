from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12


def example_get_battery():
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_bat()
        print('> battery: {} mV'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    example_get_battery()
