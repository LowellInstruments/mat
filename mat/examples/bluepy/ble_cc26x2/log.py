import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE, LOG_EN_CMD
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def log_en():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(LOG_EN_CMD)
            print('\tLOG --> {}'.format(rv))

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    log_en()
