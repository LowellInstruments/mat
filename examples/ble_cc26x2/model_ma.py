import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller_ble import LoggerControllerBLE


mac = mac_ble_cc26x2


def get_li_model():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.get_li_model()
            print('\tRLI (MA) --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    get_li_model()
