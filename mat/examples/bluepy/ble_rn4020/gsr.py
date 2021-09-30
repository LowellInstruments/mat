from mat.examples.bluepy.ble_rn4020.rn4020_shell import rn4020_shell
from mat.logger_controller import SENSOR_READINGS_CMD
from mat.examples.bluepy.ble_rn4020.macs import MAC_LOGGER_MAT1_0

mac = MAC_LOGGER_MAT1_0

if __name__ == '__main__':
    _ = [SENSOR_READINGS_CMD] * 5
    rn4020_shell(_, mac)
