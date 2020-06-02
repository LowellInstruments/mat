from mat.logger_controller_ble import LoggerControllerBLE
import bluepy.btle as btle
import time
import sys
import os
import datetime
from mat.examples.ble.simple._macs import mac


def main():
    # scan stage
    # scanner = btle.Scanner()
    # devices = scanner.scan(5.0)
    # for dev in devices:
    #     print("{} ({}) rssi {} dB".format(dev.addr, dev.addrType, dev.rssi))

    # connection stage
    while True:
        print('\nConnection attempt to {}'.format(mac))
        try:
            with LoggerControllerBLE(mac) as lc_ble:
                print('Connection --> ok')
                print('Status --> {}'.format(lc_ble.command('STS')))
                print('Stop --> {}'.format(lc_ble.command('STP')))
                print('Firmware --> {}'.format(lc_ble.command('GFV')))

                logger_time = lc_ble.get_time()
                print('Time --> {}.'.format(logger_time))
                if logger_time:
                    difference = datetime.datetime.now() - logger_time
                    if abs(difference.total_seconds()) > 60:
                        lc_ble.sync_time()
                        print('Time after sync --> {}'.format(lc_ble.get_time()))
                    else:
                        print('Logger time is up-to-date')
                else:
                    raise ValueError

                control = 'BTC 00T,0006,0000,0064'
                print('Control --> {}'.format(lc_ble.command(control)))

                folder = tools_purge_dl_folder(mac)
                files_in_logger = lc_ble.ls_ext()
                print('Files --> {}'.format(files_in_logger))
                for each in files_in_logger.items():
                    file_name = each[0]
                    file_size = each[1]
                    print('\tDownloading {}'.format(file_name))
                    lc_ble.get_file(file_name, folder, file_size)
                    time.sleep(1)

            print('Disconnecting from {}.'.format(mac))
            time.sleep(time_to_sleep * 2)

        except btle.BTLEException as be:
            print('BTLEException caught at main --> {}'.format(be))
            time.sleep(time_to_sleep)
            # comment this, or not
            sys.exit(1)
        except (TypeError, ValueError) as te:
            print('TimeException caught at main --> {}'.format(te))
            time.sleep(time_to_sleep)
            # comment this, or not
            sys.exit(2)


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
