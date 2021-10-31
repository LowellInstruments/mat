import time
import bluepy.btle as ble
from mat.bluepy.logger_controller_ble_rn4020 import LoggerControllerBLERN4020


def rn4020_shell(cmd_list: list, mac):
    try:
        with LoggerControllerBLERN4020(mac) as lc:
            for cmd in cmd_list:
                rv = lc.command(cmd)
                print('[ BLE ] {} -> {}'.format(cmd, rv))
                time.sleep(.5)
    except ble.BTLEException as ex:
        print('[ BLE ] exception -> {}'.format(ex))
