from mat.examples_ble_rn4020.simple.simple import rn4020_shell
from mat.logger_controller import SENSOR_READINGS_CMD


if __name__ == '__main__':
    _ = [SENSOR_READINGS_CMD] * 5
    rn4020_shell(_)
