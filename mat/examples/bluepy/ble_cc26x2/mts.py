import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE, MY_TOOL_SET_CMD
from mat.logger_controller import FIRMWARE_VERSION_CMD, STOP_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def mts():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))

            rv = lc.command(MY_TOOL_SET_CMD)
            print('\t\tMTS --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    mts()
