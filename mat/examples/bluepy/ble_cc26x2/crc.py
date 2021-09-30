import time
import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.crc import calculate_local_file_crc
from mat.examples.bluepy.ble_cc26x2.ls import ls_not_lid, ls_ext
from mat.logger_controller import STATUS_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


FILE_NAME = 'dummy_133.lid'


def crc(also_local=False):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(rv))
            r = lc.command('STP')
            print('\t\tSTP --> {}'.format(r))

            # 6 MHz SPI, a CRC for a 200 KB NOR file takes 6 secs
            _ = time.perf_counter()
            rv = lc.command('CRC', FILE_NAME)
            _ = time.perf_counter() - _
            s = '\t\tCRC remote --> {}, took {} ms'
            print(s.format(rv, _ * 1000))

            if also_local:
                rv = calculate_local_file_crc(FILE_NAME)
                print('\t\tCRC local --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    ls_not_lid()
    ls_ext(b'lid')
    for _ in range(1):
        crc(False)
