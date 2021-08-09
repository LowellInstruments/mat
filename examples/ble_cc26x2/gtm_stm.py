import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


def gtm_stm():
    try:
        with LoggerControllerBLE(mac) as lc_ble:

            result = lc_ble.command('STP')
            print('\tSTP --> {}'.format(result))

            rv = lc_ble.get_time()
            print('\tGTM --> {}'.format(rv))

            rv = lc_ble.sync_time()
            print('\tSTM --> {}'.format(rv))

            rv = lc_ble.get_time()
            print('\tGTM --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    gtm_stm()
