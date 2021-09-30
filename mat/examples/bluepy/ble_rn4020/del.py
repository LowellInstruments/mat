import bluepy.btle as ble

from mat.examples.bluepy.ble_rn4020.dir import ls_lid_rn4020
from mat.logger_controller import DEL_FILE_CMD
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.examples.bluepy.ble_rn4020.macs import MAC_LOGGER_MAT1_0

mac = MAC_LOGGER_MAT1_0


def delete_one_file(f):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(DEL_FILE_CMD, f)
            print('\t\tDEL --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def delete_all_lid(_ls):
    with LoggerControllerBLE(mac) as lc:
        _ls = [i.decode() for i in _ls if i.endswith(b'lid')]
        for i in _ls:
            rv = lc.command(DEL_FILE_CMD, i)
            print('\t\tDEL {} --> {}'.format(i, rv))


if __name__ == '__main__':
    # it will connect twice but, meh
    ls = ls_lid_rn4020(mac)
    delete_all_lid(ls)
