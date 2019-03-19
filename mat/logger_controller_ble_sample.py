from mat.logger_controller_ble import LoggerControllerBLE
import bluepy.btle as btle
import time
import os
import datetime


def main():
    time_to_sleep = 5
    my_logger_mac = '00:1e:c0:3d:7a:cb'

    while True:
        print('\nConnecting to {}'.format(my_logger_mac), end='')

        try:
            with LoggerControllerBLE(my_logger_mac) as lc_ble:
                print('... ok')
                print('Status --> {}'.format(lc_ble.command('STS')))
                print('Stop --> {}'.format(lc_ble.command('STP')))
                print('Firmware --> {}'.format(lc_ble.command('GFV')))

                logger_time = lc_ble.get_time()
                print('Time --> {}.'.format(logger_time))
                difference = datetime.datetime.now() - logger_time
                if abs(difference).total_seconds() > 60:
                    print('\tSyncing time...')
                    lc_ble.sync_time()

                control = 'BTC 00T,0006,0000,0064'
                print('Control --> {}'.format(lc_ble.command(control)))

                folder = tools_purge_dl_folder(my_logger_mac)
                files_in_logger = lc_ble.list_files()
                print('Files --> {}'.format(files_in_logger))
                for each in files_in_logger.items():
                    file_name = each[0].decode()
                    file_size = each[1].decode()
                    if file_name.endswith('.lid'):
                        print('\tDownloading {}'.format(file_name))
                        lc_ble.get_file(file_name, folder, file_size)
                        time.sleep(1)

            print('Disconnecting from {}.'.format(my_logger_mac))
            time.sleep(time_to_sleep * 2)

        except btle.BTLEException as be:
            print('BTLEException caught at main --> {}'.format(be))
            time.sleep(time_to_sleep)


def tools_purge_dl_folder(logger_mac):
    folder = 'dl_files/' + logger_mac.replace(':', '-')
    os.makedirs(folder, exist_ok=True)
    existing_files = os.listdir(folder)
    for each in existing_files:
        if each.endswith(".lid"):
            os.remove(os.path.join(folder, each))
    return folder


if __name__ == '__main__':
    main()
