import time
from bluepy.btle import BTLEException
from mat.examples_ble_rn4020.simple.simple import mac_def as mac
from mat.logger_controller_ble import LoggerControllerBLE


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
