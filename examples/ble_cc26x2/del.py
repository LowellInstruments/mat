import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import DEL_FILE_CMD
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


def rm(f):
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(DEL_FILE_CMD, f)
            print('\t\tDEL --> {}'.format(rv))
            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    rm('lowell_data.lid')
    rm('dummy.txt')
