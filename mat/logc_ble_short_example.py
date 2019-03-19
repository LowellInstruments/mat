from mat.logger_controller_ble import LoggerControllerBLE
import bluepy.btle as btle
import time


# variables for statistics
num_conn_ok = 0
num_conn_attempts = 0
num_dl_ok = 0
num_dl_attempts = 0


# --------------------
# infinite main loop
# --------------------
time_to_sleep = 5
my_logger_mac = '00:1e:c0:3d:7a:cb'
while True:
    num_conn_attempts += 1
    print('Connecting to {}...'.format(my_logger_mac))

    try:
        with LoggerControllerBLE(my_logger_mac) as lc_ble:
            print('\tConnection ok')
            print('Status logger: {}.'.format(lc_ble.command('STS')))
            print('Firmware logger: {}.'.format(lc_ble.command('GFV')))
            control = 'BTC 00T,0006,0000,0064'
            print('Control logger: {}.'.format(lc_ble.command(control)))
            print('List files logger: {}.'.format(lc_ble.command('DIR 00')))
            print('Get file a64KB.lid')
            lc_ble.get_file('a64KB.lid', 65536)
            time.sleep(time_to_sleep * 2)

    except btle.BTLEException as be:
        print('BTLEException caught at main --> {}'.format(be))
        time.sleep(time_to_sleep)
