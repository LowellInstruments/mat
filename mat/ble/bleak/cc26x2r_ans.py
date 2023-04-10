from mat.logger_controller import STATUS_CMD, RUN_CMD, STOP_CMD, RWS_CMD, SWS_CMD, SET_TIME_CMD, LOGGER_INFO_CMD_W, \
    DEL_FILE_CMD, FIRMWARE_VERSION_CMD, DO_SENSOR_READINGS_CMD, LOGGER_INFO_CMD, TIME_CMD, DIR_CMD, SENSOR_READINGS_CMD
from mat.logger_controller_ble import LED_CMD, FORMAT_CMD, CONFIG_CMD, MY_TOOL_SET_CMD, DWG_FILE_CMD, FILE_EXISTS_CMD, \
    WAKE_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, LOG_EN_CMD, PRF_TIME_CMD, PRF_TIME_CMD_GET, PRF_TIME_EN, BAT_CMD, WAT_CMD, \
    UP_TIME_CMD, CRC_CMD


def _check(tag, ans, n):
    return ans and len(ans) == n and ans.startswith(tag.encode())


_ck = _check


def is_cmd_done(tag, ans):
    t, a = tag, ans

    if tag == 'DWL':
        return False

    if ans == b'ERR':
        return True

    if t == STATUS_CMD:
        return _ck(t, a, 8)

    if t in (
        RUN_CMD,
        STOP_CMD,
        RWS_CMD,
        SWS_CMD,
        SET_TIME_CMD,
        'FDS',
        LOGGER_INFO_CMD_W,
        LED_CMD,
        FORMAT_CMD,
        CONFIG_CMD,
        MY_TOOL_SET_CMD,
        DEL_FILE_CMD,
        DWG_FILE_CMD,
        FILE_EXISTS_CMD
    ):
        return _ck(t, a, 6)

    if t in (
        STATUS_CMD,
        WAKE_CMD,
        ERROR_WHEN_BOOT_OR_RUN_CMD,
        LOG_EN_CMD,
        PRF_TIME_CMD,
        PRF_TIME_CMD_GET,
        PRF_TIME_EN,
        'BLA'
    ):
        return _ck(t, a, 8)

    if t in (BAT_CMD, WAT_CMD):
        return _ck(t, a, 10)

    if t in (
        FIRMWARE_VERSION_CMD,
    ):
        return _ck(t, a, 12)

    if t in (
        UP_TIME_CMD,
        CRC_CMD
    ):
        return _ck(t, a, 14)

    if t == DO_SENSOR_READINGS_CMD:
        return _ck(t, a, 18)

    if t == LOGGER_INFO_CMD:
        n = len(a) if a else 0
        return a and a.startswith(t.encode()) and n in (10, 13)

    if t in(TIME_CMD, 'FDG'):
        return _ck(t, a, 25)

    if t == DIR_CMD:
        b1, b2 = b'\x04', b'\x04\n\r'
        return a and a.endswith(b1) or a.endswith(b2)

    if t == SENSOR_READINGS_CMD:
        return a and len(a) in (38, 46)

    print('[ BLE ] is_cmd_done cannot manage', t)