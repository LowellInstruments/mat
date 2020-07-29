import bluepy.btle as ble
from mat.logger_controller import LOGGER_HSA_CMD_W, CALIBRATION_CMD
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble._macs import _macs

# used in these examples
mac = _macs['mla098']


def hsa():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command(LOGGER_HSA_CMD_W, "TMO12345")
            print('\t\tWHS --> {}'.format(result))
            result = lc_ble.command(CALIBRATION_CMD, "TMO")
            print('\t\tRHS --> {}'.format(result))
            result = lc_ble.command(CALIBRATION_CMD, "TMR")
            print('\t\tRHS --> {}'.format(result))
            result = lc_ble.command(CALIBRATION_CMD, "TMA")
            print('\t\tRHS --> {}'.format(result))
            result = lc_ble.command(CALIBRATION_CMD, "TMB")
            print('\t\tRHS --> {}'.format(result))

            # error on purpose!
            result = lc_ble.command(CALIBRATION_CMD, "TMX")
            print('\t\tRHS --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


if __name__ == '__main__':
    print('APP: start')
    hsa()
    print('APP: done')
