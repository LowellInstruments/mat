import bluepy.btle as ble
from mat.examples_ble_rn4020.simple.dir import ls_lid_rn4020
from mat.logger_controller import DEL_FILE_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_rn4020._macs import mac_def


# use default MAC or override it
mac = mac_def


def delete(f):
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(DEL_FILE_CMD, f)
            print('\t\tDEL --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    name_to_delete = '18106C9_MATP_(3).lid'
    ls_lid_rn4020()
    delete('wrong_one.lid')
    delete(name_to_delete)
