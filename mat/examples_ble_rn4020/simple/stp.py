from mat.examples_ble_rn4020.simple.simple import rn4020_shell
from mat.logger_controller import STOP_CMD


if __name__ == '__main__':
    rn4020_shell([STOP_CMD] * 2)
