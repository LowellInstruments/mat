from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.ble_logger_lowell.macs import MAC_LOGGER_DO2_0_SDI12, MAC_LOGGER_DO2_0_MODBUS


mac = MAC_LOGGER_DO2_0_MODBUS


def file_list():
    lc = LoggerControllerBLELowell(mac)
    if lc.open():
        rv = lc.ble_cmd_dir_ext('lid')
        print('list lid files: {}\n'.format(rv))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    file_list()
