import time
from bluepy.btle import BTLEException
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.examples.bluepy.ble_logger_rn4020.macs import MAC_LOGGER_MAT1_0

mac = MAC_LOGGER_MAT1_0


# this main is different, use sync_time()
if __name__ == '__main__':
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command('STP')
            print('\tSTP --> {}'.format(rv))
            time.sleep(.1)

            rv = lc.get_time()
            print('\tGTM --> {}'.format(rv))

            rv = lc.sync_time()
            print('\tSTM --> {}'.format(rv))

            rv = lc.get_time()
            print('\tGTM --> {}'.format(rv))

    except BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))
