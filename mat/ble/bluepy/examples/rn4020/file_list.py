from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
from mat.ble.bluepy.examples.cc26x2r.file_list import file_list


if __name__ == '__main__':
    for i in range(1):
        file_list(cla=LoggerControllerRN4020)
