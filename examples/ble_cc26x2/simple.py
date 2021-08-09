import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STOP_CMD
from mat.logger_controller_ble_factory import LcBLEFactory

mac = mac_ble_cc26x2


# useful to test any
my_cmd = 'MTS'


def simple():
    try:
        lc = LcBLEFactory.generate(mac)
        with lc(mac) as lc:
            rv = lc.command(STOP_CMD)
            print('\t\t{} --> {}'.format(STOP_CMD, rv))
            rv = lc.command(my_cmd)
            print('\t\t{} --> {}'.format(my_cmd, rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    simple()
