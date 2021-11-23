from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.bluepy.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.examples.macs import MAC_LOGGER_DO2_0_SDI12, MAC_LOGGER_MAT1_1


def get_mac(cla, forced=''):
    if forced:
        return forced

    if cla is LoggerControllerBLELowell:
        return MAC_LOGGER_DO2_0_SDI12

    if cla is LoggerControllerBLERN4020:
        return MAC_LOGGER_MAT1_1

