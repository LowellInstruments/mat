from mat.bluepy.logger_controller_ble_do import LoggerControllerBLEDO
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = '60:77:71:22:c8:18'



def example_file_list():
    lc = LoggerControllerBLEDO(mac)
    if lc.open():
        rv = lc.ble_cmd_dir_ext('*')
        print('list all files: {}\n'.format(rv))
        rv = lc.ble_cmd_file_list_without_lid_files()
        print('list non-lid files: {}\n'.format(rv))
        rv = lc.ble_cmd_dir_ext('lid')
        print('list lid files: {}\n'.format(rv))
        rv = lc.ble_cmd_file_list_only_lid_files()
        s = '(should be same as previous)'
        print('list lid files: {} {}\n'.format(rv, s))
    else:
        print('{} connection error'.format(__name__))
    lc.close()


if __name__ == '__main__':
    example_file_list()
