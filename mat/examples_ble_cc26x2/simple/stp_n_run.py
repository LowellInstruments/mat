import bluepy.btle as ble
from mat.logger_controller import (RUN_CMD, STOP_CMD, RWS_CMD, SWS_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples_ble_cc26x2._macs import mac_def


# use default MAC or override it
mac = mac_def


def stop_n_run(c, s):
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            r = lc_ble.command(c, s)
            print('\t\t{} --> {}'.format(c, r))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def stop(s=''):
    c = SWS_CMD if s else STOP_CMD
    stop_n_run(c, s)


def run(s=''):
    c = RWS_CMD if s else RUN_CMD
    stop_n_run(c, s)


def try_run():
    # run()
    s = '-10.123456+20.654321'
    # s = ''
    # s = 'a' * 500
    # s = 'a' * 50
    run(s)


def try_stop():
    # stop()
    s = '+30.123456-40.654321'
    # s = ''
    # s = 'b' * 500
    stop(s)


if __name__ == '__main__':
    print('APP: start')
    try_stop()
    # time.sleep(2)
    # try_run()
    # time.sleep(60)
    # try_stop()
    print('APP: done')
