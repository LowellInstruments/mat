from mat.bluepy.ble_bluepy import ble_connect_n_cmd
from mat.bluepy.logger_controller_ble_lowell import LoggerControllerBLELowell
from mat.examples.bluepy.ble_logger_do.macs import MAC_LOGGER_DO2_0_SDI12

mac = MAC_LOGGER_DO2_0_SDI12


# simple, not optimized, sequence  of commands :)
if __name__ == '__main__':
    logger_class = LoggerControllerBLELowell
    ble_connect_n_cmd(logger_class, mac, 'ble_cmd_status')
    ble_connect_n_cmd(logger_class, mac, 'ble_cmd_status')
    ble_connect_n_cmd(logger_class, mac, 'ble_cmd_status')
    ble_connect_n_cmd(logger_class, mac, 'ble_cmd_status')
    ble_connect_n_cmd(logger_class, mac, 'ble_cmd_fw_ver')

