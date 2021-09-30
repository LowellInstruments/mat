from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_MODBUS


mac = MAC_LOGGER_DO2_0_MODBUS


def example_set_time():
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_stm()
        print('> set time: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    example_set_time()
