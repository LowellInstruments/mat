from mat.examples_ble_rn4020.simple.simple import rn4020_shell
from mat.logger_controller import RUN_CMD, STATUS_CMD


if __name__ == '__main__':
    _ = [STATUS_CMD, RUN_CMD, STATUS_CMD]
    rn4020_shell(_)

