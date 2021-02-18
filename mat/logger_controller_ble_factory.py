from mat.logger_controller_ble import FAKE_MAC_CC26X2, FAKE_MAC_RN4020, LoggerControllerBLE
from mat.logger_controller_ble_dummy_cc26x2 import LoggerControllerBLEDummyCC26x2
from mat.logger_controller_ble_dummy_rn4020 import LoggerControllerBLEDummyRN4020


class LcBLEFactory:

    @staticmethod
    def generate(_mac):
        """ this returns one of our BLE CLASS, not an object """
        if _mac in [FAKE_MAC_CC26X2]:
            return LoggerControllerBLEDummyCC26x2

        if _mac in [FAKE_MAC_RN4020]:
            return LoggerControllerBLEDummyRN4020

        # it's a real logger
        return LoggerControllerBLE


# example: yep, state 'mac' twice
# -------------------------------
#   lc = LcBLEFactory.generate(mac)
#   with lc(mac) as lc:
#       rv = lc.command(STATUS_CMD)
#       print('\t\tSTS --> {}'.format(rv))
#
