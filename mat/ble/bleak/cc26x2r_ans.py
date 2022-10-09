from mat.logger_controller import *
from mat.logger_controller_ble import *
from mat.logger_controller_ble import LED_CMD, BAT_CMD


def _check(tag, ans, n):
    return ans and len(ans) == n and ans.startswith(tag.encode())


_ck = _check


def is_cmd_done(tag, ans):
    t, a = tag, ans
    if t == STATUS_CMD:
        return _ck(t, a, 8)
    if t == RUN_CMD:
        return a == b'RUN 00'
    if t == STOP_CMD:
        return a == b'STP 00'
    if t == RWS_CMD:
        return a == b'RWS 00'
    if t == SWS_CMD:
        return a == b'SWS 00'
    if t == SET_TIME_CMD:
        return a == b'STM 00'
    if t == LOGGER_INFO_CMD_W:
        return a == b'WLI 00'
    if t == LOGGER_INFO_CMD:
        n = len(a) if a else 0
        return a.startswith(t) and n in (10, 13)
    if t == LED_CMD:
        return a == b'LED 00'
    if t == STATUS_CMD:
        return _ck(t, a, 8)
    if t == FIRMWARE_VERSION_CMD:
        return _ck(t, a, 12)
    if t == BAT_CMD:
        return _ck(t, a, 10)
    if t == TIME_CMD:
        return _ck(t, a, 25)
    if tag in WAKE_CMD:
        return _ck(t, a, 8)
    if t == CRC_CMD:
        return _ck(t, a, 14)
    if t == FORMAT_CMD:
        return a == b'FRM 00'
    if t == CONFIG_CMD:
        return a == b'CFG 00'
    if t == MY_TOOL_SET_CMD:
        return a == b'MTS 00'
    if t == DEL_FILE_CMD:
        return a == b'DEL 00'
    if t == DO_SENSOR_READINGS_CMD:
        return _ck(t, a, 18)
    if t == DIR_CMD:
        b1, b2 = b'\x04', b'\x04\n\r'
        return a and a.endswith(b1) or a.endswith(b2)
    if t == SENSOR_READINGS_CMD:
        return a and len(a) in (38, 46)
    if t == ERROR_WHEN_BOOT_OR_RUN_CMD:
        return _ck(t, a, 8)
    if t == WAT_CMD:
        return _ck(t, a, 8)
    if t == UP_TIME_CMD:
        return _ck(t, a, 14)
    if t == DWG_FILE_CMD:
        return _ck(t, a, 6)

    print('[ BLE ] is_cmd_done cannot manage', t)
