import time
import bluepy.btle as ble

from mat.bluepy.logger_controller_ble import LoggerControllerBLE


def rn4020_shell(cmd_list: list, mac):
    try:
        with LoggerControllerBLE(mac) as lc:
            for cmd in cmd_list:
                rv = lc.command(cmd)
                print('\t{} -> {}'.format(cmd, rv))
                time.sleep(.5)
        return rv
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))
