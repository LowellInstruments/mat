from mat.bluepy.logger_controller_ble_lowell_utils import ble_file_list_as_dict
from mat.examples.bluepy.ble_logger_rn4020.macs import MAC_LOGGER_MAT1_0
from mat.examples.bluepy.ble_logger_rn4020.rn4020_shell import rn4020_shell
from mat.logger_controller import STOP_CMD


mac = MAC_LOGGER_MAT1_0


def ls_rn4020():
    rn4020_shell([STOP_CMD], mac)
    rn4020_shell(['DIR'], mac)


if __name__ == '__main__':
    ls_rn4020()
