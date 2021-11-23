from mat.bluepy.logger_controller_ble_rn4020 import LoggerControllerBLERN4020
from mat.examples.bluepy.ble_logger_lowell.file_delete_one import file_rm


if __name__ == '__main__':
    s = 'file_name.lid'
    file_rm(s, cla=LoggerControllerBLERN4020)
