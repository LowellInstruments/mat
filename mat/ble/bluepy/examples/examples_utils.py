from mat.ble.ble_macs import *
from mat.ble.bluepy.cc26x2r_logger_controller import LoggerControllerCC26X2R
from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020


def get_mac(cla, forced=''):
    if forced:
        return forced

    if cla is LoggerControllerCC26X2R:
        return MAC_LOGGER_DO2_1_MODBUS

    if cla is LoggerControllerRN4020:
        return MAC_LOGGER_MAT1_1

