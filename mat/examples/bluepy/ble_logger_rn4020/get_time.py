from mat.examples.bluepy.ble_logger_rn4020.rn4020_shell import rn4020_shell
from mat.logger_controller import TIME_CMD
from mat.examples.bluepy.ble_logger_rn4020.macs import MAC_LOGGER_MAT1_0

mac = MAC_LOGGER_MAT1_0

if __name__ == '__main__':
    rn4020_shell([TIME_CMD], mac)
