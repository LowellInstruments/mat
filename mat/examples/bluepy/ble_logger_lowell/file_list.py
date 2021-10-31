from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.ble_logger_lowell.macs import MAC_LOGGER_DO2_0_SDI12

mac = '60:77:71:22:c8:18'

# todo > check this example


def example_file_list():
    lc = LoggerControllerBLELowell(mac)
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
