import bluepy.btle as ble
from mat.logger_controller import (LOGGER_INFO_CMD_W,
                                   LOGGER_INFO_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['lp2']

# e.g. 1920 mV = 0x0780 --> 'BA8007'
# e.g. 2500 mV = 0x09c4 --> 'BAC409'
# e.g. 5000 mV = 0x1388 --> 'BA8813'


def bat():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command(LOGGER_INFO_CMD, "BA")
            print('\t\tRLI (BA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD_W, "BA8007")
            print('\t\tWLI (BA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD, "BA")
            print('\t\tRLI (BA) --> {}'.format(result))
            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    bat()
    print('APP: done')
