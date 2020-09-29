import time
import bluepy.btle as ble
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_rn4020._macs import mac_def


def rn4020_shell(cmd_list: list, mac=mac_def):
    try:
        with LoggerControllerBLE(mac) as lc:
            for cmd in cmd_list:
                rv = lc.command(cmd)
                print('\t{} -> {}'.format(cmd, rv))
                time.sleep(.5)
        return rv
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))
