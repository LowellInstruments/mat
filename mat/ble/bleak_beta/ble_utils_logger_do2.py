import asyncio
from mat.logger_controller import STATUS_CMD, FIRMWARE_VERSION_CMD, DIR_CMD, SET_TIME_CMD, STOP_CMD, TIME_CMD, \
    SD_FREE_SPACE_CMD, DEL_FILE_CMD, LOGGER_INFO_CMD_W, LOGGER_INFO_CMD, CALIBRATION_CMD, LOGGER_HSA_CMD_W, SWS_CMD, \
    RUN_CMD, RWS_CMD
from mat.logger_controller_ble import *
import mat.ble_utils_shared as bs


UUID_C = 'f0001132-0451-4000-b000-000000000000'
UUID_W = 'f0001131-0451-4000-b000-000000000000'
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


async def ans_rx():

    # estimate time as units of 10 milliseconds
    units = .01
    tag = bs.g_cmd.split()[0]
    _ = {
        # 3000 * 10 ms = 30 s
        MY_TOOL_SET_CMD: 3000,
        RUN_CMD: 1500,
        RWS_CMD: 1500,
        SWS_CMD: 1500,
        STOP_CMD: 1500,
    }
    # default: 1000 * 10 ms = 10 s
    till = _.get(tag, 1000)

    # leave: at timeout or _nh() says so
    while 1:
        if is_answer_done(bs.g_cmd, bs.g_ans):
            print('[ OK ] {}'.format(bs.g_cmd))
            break
        if till == 0:
            break
        if till % 500 == 0:
            print('[ .. ] {}'.format(bs.g_cmd))
        await asyncio.sleep(units)
        till -= 1


async def cmd_tx(cli, s):
    # s: 'STS \r'
    return await cli.write_gatt_char(UUID_W, s.encode())
