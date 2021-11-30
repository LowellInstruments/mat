from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
from mat.ble.bluepy.examples.cc26x2r.file_delete_one import file_rm


if __name__ == '__main__':
    s = 'file_name.lid'
    file_rm(s, cla=LoggerControllerRN4020)
