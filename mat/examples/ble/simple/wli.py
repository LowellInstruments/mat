import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple._macs import mac
from mat.logger_controller import LOGGER_INFO_CMD_W, LOGGER_INFO_CMD


def wli():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            print('\tBLE: connected')
            result = lc_ble.command(LOGGER_INFO_CMD_W, "SN1234567")
            print('\t\tWLI (SN) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD_W, "CA1234")
            print('\t\tWLI (CA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD_W, "BA5678")
            print('\t\tWLI (BA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD_W, "MA1234ABC")
            print('\t\tWLI (MA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD, "SN")
            print('\t\tRLI (SN) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD, "CA")
            print('\t\tRLI (CA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD, "BA")
            print('\t\tRLI (BA) --> {}'.format(result))
            result = lc_ble.command(LOGGER_INFO_CMD, "MA")
            print('\t\tRLI (MA) --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    wli()
    print('APP: done')
