import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD, DEL_FILE_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


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
