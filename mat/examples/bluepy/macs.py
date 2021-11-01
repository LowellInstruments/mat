from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.bluepy.logger_controller_ble_rn4020 import LoggerControllerBLERN4020


MAC_LOGGER_DO2_0_SDI12 = '60:77:71:22:c8:18'
MAC_LOGGER_DO2_0_MODBUS = '04:EE:03:6C:EF:79'
MAC_LOGGER_MAT1_0 = '00:1e:c0:6c:76:13'


def get_mac(cla, forced=''):
    if forced:
        return forced

    if cla is LoggerControllerBLELowell:
        return MAC_LOGGER_DO2_0_MODBUS

    if cla is LoggerControllerBLERN4020:
        return MAC_LOGGER_MAT1_0

