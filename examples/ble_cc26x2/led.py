import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STATUS_CMD
from mat.logger_controller_ble_factory import LcBLEFactory

mac = mac_ble_cc26x2


def led():
    try:
        lc = LcBLEFactory.generate(mac)
        with lc(mac) as lc:
            rv = lc.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(rv))
            r = lc.command('LED')
            print('\t\tLED --> {}'.format(r))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    led()
