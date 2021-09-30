import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE, MOBILE_CMD
from mat.logger_controller import FIRMWARE_VERSION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def ensure_mbl_mode_on(lc):
    rv = lc.command(MOBILE_CMD)
    print('\tMBL --> {}'.format(rv))
    if rv[1][-1] == 49:
        return
    rv = lc.command(MOBILE_CMD)
    print('\tMBL --> {}'.format(rv))


def mbl():
    try:
        with LoggerControllerBLE(mac) as lc:
            ensure_mbl_mode_on(lc)

    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    mbl()
