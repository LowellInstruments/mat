import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override



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
