from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12


def example_get_file_size(file_name):
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_siz(file_name)
        print('> get one file size: {}'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    f = 'dummy_23.lid'
    example_get_file_size(f)
