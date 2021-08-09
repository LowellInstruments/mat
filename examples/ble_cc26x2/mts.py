import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE, MY_TOOL_SET_CMD

mac = mac_ble_cc26x2


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
