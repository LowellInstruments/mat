from mat.logger_controller import RWS_CMD, RUN_CMD, SET_TIME_CMD, LOGGER_INFO_CMD_W, STOP_CMD, STATUS_CMD, SWS_CMD, \
    DEL_FILE_CMD, FIRMWARE_VERSION_CMD, TIME_CMD, REQ_FILE_NAME_CMD, LOGGER_INFO_CMD, DIR_CMD
from mat.logger_controller_ble import GET_FILE_CMD


def _check(tag, ans, n):
    if not ans:
        return False
    sw = '\n\r{}'.format(tag).encode()
    return ans and len(ans) == n and ans.startswith(sw)


_ck = _check


def is_cmd_done(tag, ans):
    t, a = tag, ans

    if ans == b'ERR':
        return True

    if t in (
        RWS_CMD,
        RUN_CMD,
        SET_TIME_CMD,
        LOGGER_INFO_CMD_W,
        GET_FILE_CMD,
    ):
        return _ck(t, a, 10)

    if t in (
            STOP_CMD,
            STATUS_CMD,
            SWS_CMD
    ):
        return _ck(t, a, 12)

    if t == DEL_FILE_CMD:
        # this one is a bit different
        cond = b'DEL 00' in a
        return a and len(a) in (10, 12) and cond

    if t == FIRMWARE_VERSION_CMD:
        return b'\n\rGFV' in a and a.endswith(b'\r\n')

    if t == TIME_CMD:
        return _ck(t, a, 29)

    if t == REQ_FILE_NAME_CMD:
        if b'ERR 00' in a:
            # simply no ongoing lid file
            return True
        # a: b'\n\rRFN 1718060DB_MATP_1H_(0)z.lid\n\r\n'
        return b'.lid' in a

    if t == LOGGER_INFO_CMD:
        n = len(a) if a else 0
        return a.startswith(t) and n in (14, 17)

    if t == DIR_CMD:
        b1, b2 = b'\x04', b'\x04\n\r'
        return a and a.endswith(b1) or a.endswith(b2)

    if t == 'BTC':
        return a == b'\n\rCMD\r\nAOK\r\nMLDP\r\n'

    print('[ BLE ] RN4020 is_cmd_done cannot manage', t)
