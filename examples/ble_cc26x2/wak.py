from examples.ble_cc26x2._example_macs import mac_ble_cc26x2
from mat.logger_controller import STOP_CMD, RUN_CMD
from mat.logger_controller_ble import LoggerControllerBLE, WAKE_CMD

mac = mac_ble_cc26x2


def _stp():
    with LoggerControllerBLE(mac) as lc:
        rv = lc.command(STOP_CMD)
        print('\tSTP --> {}'.format(rv))


def _run():
    with LoggerControllerBLE(mac) as lc:
        rv = lc.command(RUN_CMD)
        print('\tRUN --> {}'.format(rv))


def ensure_wak_is_on():
    with LoggerControllerBLE(mac) as lc:
        # rv -> [b'WAK', b'0201']
        rv = lc.command(WAKE_CMD)
        print(rv)
        if len(rv) != 2:
            print('error WAK cmd')
            return False
        wak_is_on = rv[1].decode()[-1]
        rv = wak_is_on == '1'
        s = 'ON' if rv else 'OFF, enabling it...'
        print('\twake mode is {}'.format(s))
        return rv


if __name__ == '__main__':
    if not ensure_wak_is_on():
        ensure_wak_is_on()
    # _run()
    # for i in reversed(range(15)):
    #     time.sleep(1)
    #     print('{} '.format(i), end='')
    # print('\n')
    # _stp()