import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD, LOGGER_INFO_CMD_W, STOP_CMD, LOGGER_INFO_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def wli():
    try:
        with LoggerControllerBLE(mac) as lc:
            print('\tBLE: connected')
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))
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
    wli()
