import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE, SIZ_CMD
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def siz():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(SIZ_CMD, 'MAT.cfg')
            print('\t\tSIZ --> {}'.format(rv))
            rv = lc.command(SIZ_CMD, 'not_there_file.txt')
            print('\t\tSIZ --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    siz()
