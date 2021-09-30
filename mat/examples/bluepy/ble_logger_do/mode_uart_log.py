from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12

def example_enable_uart_log():
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_toggle_mode_uart_logging()
        print('> log enabled: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    example_enable_uart_log()
