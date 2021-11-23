from mat.bluepy.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.examples.bluepy.ble_logger_lowell.file_list import file_list


if __name__ == '__main__':
    for i in range(10):
        file_list(cla=LoggerControllerBLERN4020)
