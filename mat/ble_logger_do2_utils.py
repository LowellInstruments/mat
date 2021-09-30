from mat.examples.bleak.do2.macs import MAC_DO2_0_DUMMY
from mat.logger_controller import STATUS_CMD, FIRMWARE_VERSION_CMD, DIR_CMD, SET_TIME_CMD, STOP_CMD, TIME_CMD, \
    SD_FREE_SPACE_CMD, DEL_FILE_CMD, LOGGER_INFO_CMD_W, LOGGER_INFO_CMD, CALIBRATION_CMD, LOGGER_HSA_CMD_W, SWS_CMD, \
    RUN_CMD
from mat.ble_commands import *


UUID_C = 'f0001132-0451-4000-b000-000000000000'
UUID_W = 'f0001131-0451-4000-b000-000000000000'
ENGINE_CMD_BYE = 'cmd_bye'
ENGINE_CMD_CON = 'cmd_connect'
ENGINE_CMD_DISC = 'cmd_disconnect'
ENGINE_CMD_SCAN = 'cmd_scan'
ENGINE_CMD_EXC = 'exc_ble_engine'
MAX_MTU_SIZE = 247


def ble_cmd_dir_result_as_dict(ls: bytes) -> dict:
    if b'ERR' in ls:
        return {'ERR': 0}

    # ls : b'\n\r.\t\t\t0\n\r\n\r..\t\t\t0\n\r\n\rMAT.cfg\t\t\t189\n\r\x04\n\r'
    d = {}
    i = 0
    ls = ls.split()

    # iterate name and size pairs
    while i < len(ls):
        name = ls[i]
        if name in [b'\x04']:
            break
        name = ls[i].decode()
        size = int(ls[i + 1].decode())
        if name not in ('.', '..'):
            d[name] = size
        i += 2
    # d: { 'MAT.cfg': 189 }
    return d


def is_answer_done(cmd, ans):

    done = False
    tag = cmd.split()[0]
    tan = ans[:3].decode()

    if ans in (b'ERR', b'INV'):
        done = True
        return done

    if tan == tag == STATUS_CMD and len(ans) == 8:
        done = True
    if tan == tag == FIRMWARE_VERSION_CMD and len(ans) == 12:
        done = True
    if tan == tag == DWG_FILE_CMD and len(ans) == 6:
        done = True
    if tan == tag == SET_TIME_CMD and len(ans) == 6:
        done = True
    if tan == tag == STOP_CMD and len(ans) == 6:
        done = True
    if tan == tag == LED_CMD and len(ans) == 6:
        done = True
    if tan == tag == OXYGEN_SENSOR_CMD and len(ans) == 18:
        done = True
    if tan == tag == TIME_CMD and len(ans) == 25:
        done = True
    if tan == tag == SLOW_DWL_CMD and len(ans) == 8:
        done = True
    if tan == tag == FORMAT_CMD and len(ans) == 6:
        done = True
    if tan == tag == MY_TOOL_SET_CMD and len(ans) == 6:
        done = True
    if tan == tag == BAT_CMD and len(ans) == 10:
        done = True
    if tan == tag == SD_FREE_SPACE_CMD and len(ans) == 14:
        done = True
    if tan == tag == DEL_FILE_CMD and len(ans) == 6:
        done = True
    if tan == tag == LOGGER_INFO_CMD_W and len(ans) == 6:
        done = True
    if tan == tag == LOGGER_INFO_CMD and len(ans) in (10, 13):
        # ans: b'RLI 045678'
        done = True
    if tan == tag == CONFIG_CMD and len(ans) == 6:
        done = True
    if tan == tag == CALIBRATION_CMD and len(ans) == 11:
        done = True
    if tan == tag == LOGGER_HSA_CMD_W and len(ans) == 6:
        done = True
    if tan == tag == LOG_EN_CMD and len(ans) == 8:
        done = True
    if tan == tag == MOBILE_CMD and len(ans) == 8:
        done = True
    if tan == tag == SIZ_CMD:
        done = True
    if tan == tag == WAKE_CMD and len(ans) == 8:
        done = True
    if tan == tag == SWS_CMD and len(ans) == 6:
        done = True
    if tan == tag == RUN_CMD and len(ans) == 6:
        done = True
    if tan == tag == GET_SENSOR_INTERVAL:
        done = True
    if tan == tag == GET_SENSOR_DO_INTERVAL:
        done = True
    if tan == tag == GET_COMMON_SENSOR_INTERVAL:
        done = True

    # slightly special ones, no tag_answer used
    if tag == DIR_CMD and ans.endswith(b'\x04\n\r'):
        done = True
    if tag == DWL_CMD and len(ans) == 2048:
        done = True

    # debug
    # if tag != DWL_CMD:
    #     s = '\t\t(en) dbg: tag {} ans_len {} g_ans_done {}'
    #     print(s.format(tag, len(ans), done))

    return done


class BleakClientDummyDO2:
    def __init__(self, mac):
        self.address = mac

    def connect(self):
        return self.address == MAC_DO2_0_DUMMY

    def disconnect(self):
        self.address = None


class EngineException(Exception):
    pass
