import bluepy.btle as ble
from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STATUS_CMD, DO_SENSOR_READINGS_CMD
from mat.logger_controller_ble_factory import LcBLEFactory

mac = mac_ble_cc26x2


def gdo():
    try:
        lc = LcBLEFactory.generate(mac)
        with lc(mac) as lc:
            rv = lc.command(DO_SENSOR_READINGS_CMD)
            print('\t\t{} --> {}'.format(DO_SENSOR_READINGS_CMD, rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    gdo()
