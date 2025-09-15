from re import findall
from mat.logger_controller import (
    STATUS_CMD, RUN_CMD, STOP_CMD, RWS_CMD, SWS_CMD, SET_TIME_CMD,
    LOGGER_INFO_CMD_W, DEL_FILE_CMD, FIRMWARE_VERSION_CMD,
    LOGGER_INFO_CMD, TIME_CMD, DIR_CMD, SENSOR_READINGS_CMD)
from mat.logger_controller_ble import (
    LED_CMD, FORMAT_CMD, CONFIG_CMD, MY_TOOL_SET_CMD, DWG_FILE_CMD, FILE_EXISTS_CMD,
    WAKE_CMD, ERROR_WHEN_BOOT_OR_RUN_CMD, LOG_EN_CMD,
    BAT_CMD, WAT_CMD, UP_TIME_CMD, CRC_CMD, SET_CALIBRATION_CMD, GET_CALIBRATION_CMD,
    DEPLOYMENT_NAME_SET_CMD, DEPLOYMENT_NAME_GET_CMD, PRESSURE_SENSOR_CMD,
    OXYGEN_SENSOR_CMD, TEMPERATURE_SENSOR_CMD, GET_PRF_CONFIGURATION_CMD,
    SET_PRF_CONFIGURATION_CMD)


def _check(tag, ans, n):
    return ans and len(ans) == n and ans.startswith(tag.encode())


_ck = _check


def is_cmd_done(tag, ans):
    t, a = tag, ans

    # this condition must be up here
    if ans == b'ERR':
        return True

    if tag == 'DWL':
        return False

    if tag == 'GAB':
        return _ck(t, a, 198)

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
            'DHA',
            CONFIG_CMD,
            MY_TOOL_SET_CMD,
            DEL_FILE_CMD,
            DWG_FILE_CMD,
            FILE_EXISTS_CMD,
            SET_CALIBRATION_CMD,
            SET_PRF_CONFIGURATION_CMD,
            DEPLOYMENT_NAME_SET_CMD,
            'SSP',
            'BNA'
    ):
        return _ck(t, a, 6)

    if t in (
        STATUS_CMD,
        WAKE_CMD,
        ERROR_WHEN_BOOT_OR_RUN_CMD,
        LOG_EN_CMD,
        'HBW',
        'GWF',
        'PER',
        'ARA',
        'ARP',
        'ARF',
        'TSL',
        'TST',
        'OAE',
        'OAF'
    ):
        return _ck(t, a, 8)

    if t in ('GSC', ):
        return _ck(t, a, 22)

    if t in (BAT_CMD, WAT_CMD):
        return _ck(t, a, 10)

    if t in (
        FIRMWARE_VERSION_CMD,
    ):
        return _ck(t, a, 12)

    if t in (
        UP_TIME_CMD,
        'RTM',
        CRC_CMD
    ):
        return _ck(t, a, 14)

    if t == OXYGEN_SENSOR_CMD:
        return _ck(t, a, 18)

    if t in (PRESSURE_SENSOR_CMD, TEMPERATURE_SENSOR_CMD):
        return _ck(t, a, 10)

    if t == LOGGER_INFO_CMD:
        n = len(a) if a else 0
        return a and a.startswith(t.encode()) and n in (10, 13)

    if t == 'RFN':
        return a and a.startswith(b'RFN')

    if t == 'GLT':
        return a and a.startswith(b'GLT') and len(a) == 7

    if t in (TIME_CMD, 'FDG'):
        return _ck(t, a, 25)

    if t in (DIR_CMD, '__A'):
        b1, b2 = b'\x04', b'\x04\n\r'
        return a and a.endswith(b1) or a.endswith(b2)

    if t == SENSOR_READINGS_CMD:
        return a and len(a) in (38, 46)

    if t == GET_CALIBRATION_CMD:
        return a and len(a) == (5 * 33) + 6

    if t == GET_PRF_CONFIGURATION_CMD:
        return a and len(a) == (5 * 9) + 6

    if t == DEPLOYMENT_NAME_GET_CMD:
        return a and len(a) == 9

    if t == 'XOD':
        return _ck(t, a, 10)

    if t == 'GWC':
        return a and len(a) in (9, 10, 12, 16)

    if t == 'GDX':
        return a and len(findall(r"[-+]?(?:\d*\.*\d+)", a.decode())) == 3

    if t == 'MAC':
        print('len_mac', len(a))
        return a and a.startswith(b'MAC') and len(a) == 6 + 17

    if t == '__B':
        # a: b'__B 200020000000F072022/08/25 12:13:55'
        # [4:6] = 20 length
        # [6]   = 0  was it running
        # [7:15] = 02000000 uptime
        # [15:19] = 0F07 bat_str
        # [19:] = 2022/08/25 12:13:55 what was gtm
        return a and a.startswith(b'__B') and len(a) == 38

    if t == 'BEH':
        return a and a.startswith(b'BEH')

    print(f'[ BLE ] CC26X2R is_cmd_done() cannot manage {t}')
