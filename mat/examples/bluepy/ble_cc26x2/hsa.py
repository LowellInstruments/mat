import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD, LOGGER_HSA_CMD_W, CALIBRATION_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


def hsa():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(LOGGER_HSA_CMD_W, "TMO12345")
            print('\t\tWHS --> {}'.format(rv))
            rv = lc.command(CALIBRATION_CMD, "TMO")
            print('\t\tRHS --> {}'.format(rv))
            # rv = lc.command(CALIBRATION_CMD, "TMR")
            # print('\t\tRHS --> {}'.format(rv))
            # rv = lc.command(CALIBRATION_CMD, "TMA")
            # print('\t\tRHS --> {}'.format(rv))
            # rv = lc.command(CALIBRATION_CMD, "TMB")
            # print('\t\tRHS --> {}'.format(rv))

            # error on purpose!
            # rv = lc.command(CALIBRATION_CMD, "TMX")
            # print('\t\tRHS --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    hsa()
