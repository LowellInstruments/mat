import bluepy.btle as ble
from mat.logger_controller import (STATUS_CMD,
                                   RUN_CMD, STOP_CMD, RWS_CMD, SWS_CMD)
from mat.logger_controller_ble import LoggerControllerBLE
from mat.examples.ble.simple._macs import mac


def status():
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            result = lc_ble.command(STATUS_CMD)
            print('\t\tSTS --> {}'.format(result))
    except ble.BTLEException as ex:
        print('BLE: connect exception --> {}'.format(ex))


def stop_n_run(c, s):
    try:
        with LoggerControllerBLE(mac) as lc_ble:
            r = lc_ble.command(c, s, retries=1)
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

    i = 1
    # i = 100
    for _ in range(i):
        status()

    # try_stop()
    # time.sleep(2)
    # try_run()
    # time.sleep(60)
    # try_stop()
    print('APP: done')
