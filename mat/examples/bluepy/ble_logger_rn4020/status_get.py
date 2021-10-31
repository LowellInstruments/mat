from mat.examples.bleak.mat1.macs import MAC_MAT1_0
from mat.examples.bluepy.ble_logger_rn4020.rn4020_shell import rn4020_shell
from mat.logger_controller import STATUS_CMD


mac = MAC_MAT1_0


if __name__ == '__main__':
    rn4020_shell([STATUS_CMD] * 3, mac)
