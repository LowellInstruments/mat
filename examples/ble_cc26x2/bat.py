import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE, BAT_CMD

mac = mac_ble_cc26x2


def bat():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))
            rv = lc.command(BAT_CMD)
            print('\t\tBAT --> {}'.format(rv))
            b = rv[1].decode()[-2:] + rv[1].decode()[-4:-2]
            print('0x{} == {} mV'.format(b, int(b, 16)))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    bat()
