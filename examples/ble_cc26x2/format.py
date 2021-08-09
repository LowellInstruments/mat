import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


def frm():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\tSTP --> {}'.format(rv))

            rv = lc.sync_time()
            print('\t\tSTM --> {}'.format(rv))

            rv = lc.get_time()
            print('\t\tGTM --> {}'.format(rv))

            rv = lc.command('FRM')
            print('\t\tFRM --> {}'.format(rv))

            print('\tBLE: sleep 3s to disconnect to give logger time...')
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    frm()
