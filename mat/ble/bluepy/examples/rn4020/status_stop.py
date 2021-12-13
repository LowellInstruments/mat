from mat.ble.bluepy.rn4020_logger_controller import LoggerControllerRN4020
from mat.ble.bluepy.examples.cc26x2r.status_stop import stop


if __name__ == '__main__':
    stop(cla=LoggerControllerRN4020)
