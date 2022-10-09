from mat.logger_controller import *


def _check(tag, ans, n):
    if not ans:
        return False
    sw = '\n\r{}'.format(tag).encode()
    return ans and len(ans) == n and ans.startswith(sw)


_ck = _check


def is_cmd_done(tag, ans):
    t, a = tag, ans

    if t in (
            STOP_CMD,
            STATUS_CMD
    ):
        return _ck(t, a, 12)
    if t in (
        RWS_CMD,
        RUN_CMD,
        SWS_CMD,
        SET_TIME_CMD,
        LOGGER_INFO_CMD_W,
        DEL_FILE_CMD,

    ):
        return _ck(t, a, 10)
    if t == TIME_CMD:
        return _ck(t, a, 29)
    if t == LOGGER_INFO_CMD:
        n = len(a) if a else 0
        return a.startswith(t) and n in (14, 17)
    if t == FIRMWARE_VERSION_CMD:
        return _ck(t, a, 16)
    if t == DIR_CMD:
        b1, b2 = b'\x04', b'\x04\n\r'
        return a and a.endswith(b1) or a.endswith(b2)

    print('[ BLE ] is_cmd_done cannot manage', t)
