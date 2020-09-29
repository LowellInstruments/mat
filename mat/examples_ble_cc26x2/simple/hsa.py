import bluepy.btle as ble
from mat.logger_controller import LOGGER_HSA_CMD_W, CALIBRATION_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def hsa():
    try:
        with LoggerControllerBLE(mac) as lc:
            rv = lc.command(LOGGER_HSA_CMD_W, "TMO12345")
            print('\t\tWHS --> {}'.format(rv))
            rv = lc.command(CALIBRATION_CMD, "TMO")
            print('\t\tRHS --> {}'.format(rv))
            rv = lc.command(CALIBRATION_CMD, "TMR")
            print('\t\tRHS --> {}'.format(rv))
            rv = lc.command(CALIBRATION_CMD, "TMA")
            print('\t\tRHS --> {}'.format(rv))
            rv = lc.command(CALIBRATION_CMD, "TMB")
            print('\t\tRHS --> {}'.format(rv))

            # error on purpose!
            rv = lc.command(CALIBRATION_CMD, "TMX")
            print('\t\tRHS --> {}'.format(rv))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    hsa()
    print('APP: done')
