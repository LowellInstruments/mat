import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import LOGGER_INFO_CMD_W, LOGGER_INFO_CMD
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def wli():
    try:
        with LoggerControllerBLE(mac) as lc:
            print('\tBLE: connected')
            rv = lc.command(LOGGER_INFO_CMD_W, "SN1234567")
            print('\t\tWLI (SN) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD_W, "CA1234")
            print('\t\tWLI (CA) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD_W, "BA5678")
            print('\t\tWLI (BA) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD_W, "MA1234ABC")
            print('\t\tWLI (MA) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD, "SN")
            print('\t\tRLI (SN) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD, "CA")
            print('\t\tRLI (CA) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD, "BA")
            print('\t\tRLI (BA) --> {}'.format(rv))
            rv = lc.command(LOGGER_INFO_CMD, "MA")
            print('\t\tRLI (MA) --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    wli()
    print('APP: done')
