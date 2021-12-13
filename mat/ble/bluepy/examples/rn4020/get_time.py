from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
from mat.ble.bluepy.examples.cc26x2r.get_time import get_time


if __name__ == '__main__':
    get_time(cla=LoggerControllerRN4020)
