import bluepy.btle as ble
from mat.bluepy.logger_controller_ble import LoggerControllerBLE
from mat.logger_controller import FIRMWARE_VERSION_CMD, STOP_CMD, SWS_CMD, RWS_CMD, RUN_CMD
from macs import mac


# override if you want
# mac_override = '11:22:33:44:55:66'
# mac = mac_override


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
    try_stop()
    # time.sleep(2)
    #try_run()
    # time.sleep(60)
    # try_stop()
