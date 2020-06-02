import bluepy.btle as ble
from mat.logger_controller import (
    DEL_FILE_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple._macs import mac


def rm(f):
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            rv = lc_ble.command(DEL_FILE_CMD, f)
            print('\t\tDEL --> {}'.format(rv))
            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    rm('1234567_big.lid')
    rm('dummy.txt')
    print('APP: done')
